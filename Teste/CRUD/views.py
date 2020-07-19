from django.http import HttpResponse
from .models import Parada, Linha, Veiculo, PosicaoVeiculo, Chave
from .forms import ParadaForm, LinhaForm, VeiculoForm, PosicaoForm
from django.views.decorators.csrf import csrf_exempt
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from decimal import Decimal
from .utility import distance, sort_key, decode_utf8
import csv

def list_stops(request):
    """Retorna uma relação Id - Name com todas as paradas no banco"""
    if request.method == 'POST':
        return HttpResponse("Não há método POST disponível nesse link, tente GET.")
    stops = Parada.objects.values_list("Id", "Name")
    retorno = 'Id - Name\n'
    for k in stops:
        retorno += (str(k[0])+' - '+k[1]+'\n')
    return HttpResponse(retorno, content_type='text/plain')

def show_stop_info(request, id):
    """Dado um Id, retorna todas as informações sobre a parada que tenha esse Id. Se não existir parada
    com esse Id, retorna uma mensagem de erro."""
    try:
        if request.method == 'POST':
            return HttpResponse("Não há método POST disponível nesse link, tente GET.")
        stop = Parada.objects.get(Id=id)
        info = 'Id='+str(stop.Id)+'\nName='+stop.Name+'\nLatitude='+str(stop.Latitude)+'\nLongitude='+str(stop.Longitude)
        return HttpResponse(info, content_type='text/plain')
    except Parada.DoesNotExist:
        return HttpResponse("Não existe parada com este Id.")
    except Exception as ex:
        return HttpResponse(ex)

def lines_per_stop(request, id):
    """Dado um Id, retorna todas as linhas que passam pela parada o Id fornecido. Caso não exista parada
    com esse Id, retorna uma mensagem de erro."""
    try:
        if request.method == 'POST':
            return HttpResponse("Não há método POST disponível nesse link, tente GET.")
        stop = Parada.objects.get(Id=id)
        info = 'Id - Name\n'
        conjunto = stop.parada_linha.all()
        for a in conjunto:
            info += (str(a.Id)+' - '+a.Name+'\n')
        return HttpResponse(info[:-1])
    except Parada.DoesNotExist:
        return HttpResponse("Não existe parada com este Id.")
    except Exception as ex:
        return HttpResponse(ex)

@csrf_exempt
def new_stop(request):
    """"Tenta criar uma nova parada utilizando dados do corpo do POST. Se não houver todos as
    informações necessárias, retorna um erro. Se a inserção comprometer a integridade do banco
    de dados, retorna um erro. Caso contrário, adiciona a parada no banco."""
    try:
        if request.method == 'GET':
            return HttpResponse("Não há método GET disponível nesse link, tente POST.")
        chave = request.POST['auth']
        if not Chave.objects.filter(Token=chave).exists():
            return HttpResponse("Chave não validada.")
        form = ParadaForm(request.POST or None)
        if form.is_valid():
            form.save()
            return HttpResponse("Parada adicionada com sucesso.")
        return HttpResponse("Parâmetros incorretos ou Id já existente, não foi possível adicionar a parada nova.")
    except IntegrityError:
        return HttpResponse("Ja existe uma parada com esse Id, não foi possível adicionar a parada nova.")
    except KeyError:
        return HttpResponse("Chave não fornecida")
    except Exception as ex:
        return HttpResponse(ex)

@csrf_exempt
def update_stop(request, id):
    """Tenta atualizar a parada com o id passado utilizando parâmetros do POST. Não é necessário
    preencher todos os dados, só os que deseja atualizar. Se não houver a parada solicitada ou se
    os novos dados comprometerem a integridade do banco, retorna um erro."""
    try:
        if request.method == 'GET':
            return HttpResponse("Não há método GET disponível nesse link, tente POST.")
        chave = request.POST['auth']
        if not Chave.objects.filter(Token=chave).exists():
            return HttpResponse("Chave não validada.")
        stop = Parada.objects.get(pk=id)
        lat = Decimal(request.POST.get('Latitude', stop.Latitude))
        longi = Decimal(request.POST.get('Longitude', stop.Longitude))
        Id = int(request.POST.get('Id', id))
        name = request.POST.get('Name', stop.Name)
        updated_stop = {'Id':Id, 'Name':name, 'Longitude':longi, 'Latitude':lat}
        if Id != id:
            return HttpResponse('Não é permitido modificar o Id.')
        form = ParadaForm(updated_stop or None, instance=stop)
        if form.is_valid():
            form.save()
            return HttpResponse("Parada atualizada com sucesso.")
        return HttpResponse(("Valores inconsistentes ou nomes incorretos de parâmetro, não foi possível modificar a parada original."))
    except Parada.DoesNotExist as ex:
        return HttpResponse("Nao existe parada com esse Id")
    except KeyError:
        return HttpResponse("Chave não fornecida.")
    except Exception as ex:
        return HttpResponse(ex)

@csrf_exempt
def delete_stop(request, id):
    """Remove a parada com o id informado, caso ela exista. Caso contrário, retorna um erro."""
    try:
        stop = Parada.objects.get(Id=id)
        chave = request.POST['auth']
        if Chave.objects.filter(Token=chave).exists() and request.method == 'POST':
            nome = 'Parada '+str(stop.Id)+' removida com sucesso.'
            stop.delete()
            return HttpResponse(nome)
        return HttpResponse("Chave não validada ou método inválido.")
    except Parada.DoesNotExist:
        return HttpResponse("Nao existe parada com esse Id")
    except KeyError:
        return HttpResponse("Chave de autenticação não fornecida ou utilizou GET.")
    except Exception as ex:
        return HttpResponse(ex)

@csrf_exempt
def import_stops(request):
    try:
        if request.method == 'GET':
            return HttpResponse("Não há método GET disponível nesse link, tente POST.")
        chave = request.POST['auth']
        if not Chave.objects.filter(Token=chave).exists():
            return HttpResponse("Chave não validada.")
        lines = csv.reader(decode_utf8(request.FILES['file']))
        stop={}
        valid = ''
        invalid = ''
        for i in lines:
            Id=i[0]
            stop['Id']=int(Id)
            stop['Name']=i[1]
            stop['Latitude']=Decimal(i[2])
            stop['Longitude']=Decimal(i[3])
            form = ParadaForm(stop or None)
            if form.is_valid():
                form.save()
                valid += (Id+'\n')
            else:
                invalid += (Id+'\n')
        return HttpResponse('Adicionadas:\n'+valid[:-1]+'Inválidas:\n'+invalid[:-1],content_type='text/plain')
    except KeyError:
        return HttpResponse("Chave de autenticação ou arquivo não fornecidos.")
    except Exception as ex:
        return HttpResponse(ex)

@csrf_exempt
def import_stops_update(request):
    try:
        if request.method == 'GET':
            return HttpResponse("Não há método GET disponível nesse link, tente POST.")
        chave = request.POST['auth']
        if not Chave.objects.filter(Token=chave).exists():
            return HttpResponse("Chave não validada.")
        lines = csv.reader(decode_utf8(request.FILES['file']))
        stop={}
        valid = ''
        invalid = ''
        for i in lines:
            Id=i[0]
            try:
                old_stop = Parada.objects.get(pk=int(Id))
                stop['Id']=old_stop.Id
                if i[1]!='':
                    stop['Name']=i[1]
                else:
                    stop['Name']=old_stop.Name
                if i[2]!='':
                    stop['Latitude']=Decimal(i[2])
                else:
                    stop['Latitude']=old_stop.Latitude
                if i[3]!='':
                    stop['Longitude']=Decimal(i[3])
                else:
                    stop['Longitude']=old_stop.Longitude
                form = ParadaForm(stop or None,instance=old_stop)
                if form.is_valid():
                    form.save()
                    valid += (Id+'\n')
                else:
                    invalid += (Id+'\n')
            except:
                invalid += (Id+'\n')
        return HttpResponse('Atualizadas:\n'+valid[:-1]+'Inválidas:\n'+invalid[:-1],content_type='text/plain')
    except KeyError:
        return HttpResponse("Chave de autenticação ou arquivo não fornecidos.")
    except Exception as ex:
        return HttpResponse(ex)

def list_lines(request):
    """Retorna uma relação Id - Name com todas as linhas no banco"""
    if request.method == 'POST':
        return HttpResponse("Não há método POST disponível nesse link, tente GET.")
    lines = Linha.objects.values_list("Id", "Name")
    retorno = 'Id - Name\n'
    for k in lines:
        retorno += (str(k[0])+' - '+k[1]+'\n')
    return HttpResponse(retorno, content_type='text/plain')

def show_line_info(request, id):
    """Dado um Id, retorna todas as informações sobre a linha que tenha esse Id. Se não existir linha
    com esse Id, retorna uma mensagem de erro."""
    try:
        if request.method == 'POST':
            return HttpResponse("Não há método POST disponível nesse link, tente GET.")
        line = Linha.objects.get(Id=id)
        info = 'Id='+str(line.Id)+'\nName='+line.Name+'\nParadas=['
        for i in line.Paradas.all():
            info += (str(i.Id)+',')
        if info[-1] != '[':
            info = info[:-1]+']'
        else:
            info += ']'
        return HttpResponse(info, content_type='text/plain')
    except Linha.DoesNotExist:
        return HttpResponse("Não existe parada com este Id.")
    except Exception as ex:
        return HttpResponse(ex)

def vehicles_per_line(request, id):
    """Dado um Id, retorna todas os veículos vinculados à linha com Id fornecido. Caso não exista linha
    com esse Id, retorna uma mensagem de erro."""
    try:
        if request.method == 'POST':
            return HttpResponse("Não há método POST disponível nesse link, tente GET.")
        line = Linha.objects.get(Id=id)
        info = 'Id - Name\n'
        conjunto = line.linha_veiculo.all()
        for a in conjunto:
            info += (str(a.Id)+' - '+a.Name+'\n')
        return HttpResponse(info[:-1])
    except Parada.DoesNotExist:
        return HttpResponse("Não existe linha com este Id.")
    except Exception as ex:
        return HttpResponse(ex)
@csrf_exempt
def new_line(request):
    """"Tenta criar uma nova linha utilizando dados do corpo do POST. Se não houver todos as
    informações necessárias, retorna um erro. Se a inserção comprometer a integridade do banco
    de dados, retorna um erro. Caso contrário, adiciona a linha no banco."""
    try:
        if request.method == 'GET':
            return HttpResponse("Não há método GET disponível nesse link, tente POST.")
        chave = request.POST['auth']
        if not Chave.objects.filter(Token=chave).exists():
            return HttpResponse("Chave não validada.")
        form = LinhaForm(request.POST or None)
        if form.is_valid():
            form.save()
            return HttpResponse("Linha adicionada com sucesso.")
        return HttpResponse("Parâmetros incorretos ou Id já existente, não foi possível adicionar a linha nova.")
    except KeyError:
        return HttpResponse("Chave não fornecida.")
    except Exception as ex:
        return HttpResponse(ex)

@csrf_exempt
def update_line(request, id):
    """Tenta atualizar a parada com o id passado utilizando parâmetros do POST. Não é necessário
    preencher todos os dados, só os que deseja atualizar. Caso seja inserida alguma parada, ela
    será adicionada às paradas originais referentes à linha. Se não houver a linha solicitada ou se
    os novos dados comprometerem a integridade do banco, retorna um erro."""
    try:
        if request.method == 'GET':
            return HttpResponse("Não há método GET disponível nesse link, tente POST.")
        chave = request.POST['auth']
        if not Chave.objects.filter(Token=chave).exists():
            return HttpResponse("Chave não validada.")
        line = Linha.objects.get(pk=id)
        Id = int(request.POST.get('Id', id))
        name = request.POST.get('Name', line.Name)
        paradas = request.POST.getlist('Paradas', None)
        if paradas is None:
            paradas = line.Paradas.all()
        else:
            paradas += line.Paradas.all()
        updated_line = {'Id':Id, 'Name':name, 'Paradas':paradas}
        if Id != id:
            return HttpResponse('Não é permitido modificar o Id.')   
        form = LinhaForm(updated_line or None, instance=line)
        if form.is_valid():
            form.save()
            return HttpResponse("Linha atualizada com sucesso.")
        return HttpResponse(("Valores inconsistentes, não foi possível modificar a linha original."))
    except Linha.DoesNotExist as ex:
        return HttpResponse("Nao existe linha com esse Id")
    except KeyError:
        return HttpResponse("Chave não fornecida.")
    except Exception as ex:
        return HttpResponse(ex)

@csrf_exempt
def remove_stop_from_line(request, id):
    """Remove as paradas passadas pelo POST da linha com id passado. Se não houver a linha,
    retorna um erro. Se algum parada não pertencer a linha, ela é ignorada."""
    try:
        if request.method == 'GET':
            return HttpResponse("Não há método GET disponível nesse link, tente POST.")
        chave = request.POST['auth']
        if not Chave.objects.filter(Token=chave).exists():
            return HttpResponse("Chave não validada.")
        line = Linha.objects.get(pk=id)
        paradas_remover = request.POST.getlist('Paradas')
        removeu = False
        for i in paradas_remover:
            a = line.Paradas.get(pk=i) 
            if a is not None:
                line.Paradas.remove(a)
                removeu = True
        if removeu:
            return HttpResponse('Paradas com Ids válidos foram desvinculadas da linha.')
        else:
            return HttpResponse('Nenhum parada desvinculada da linha, pois Ids não bateram')
    except Parada.DoesNotExist:
        return HttpResponse('Não há nenhuma parada vinculada à essa linha.')
    except KeyError:
        return HttpResponse("Chave não fornecida.")
    except Exception as ex:
        return HttpResponse(ex)

@csrf_exempt
def delete_line(request, id):
    """Remove a linha com o id informado, caso ela exista. Caso contrário, retorna um erro."""    
    try:
        line = Linha.objects.get(Id=id)
        chave = request.POST['auth']
        if Chave.objects.filter(Token=chave).exists() and request.method == 'POST':
            nome = 'Linha '+str(line.Id)+' removida com sucesso.'
            line.delete()
            return HttpResponse(nome)
        return HttpResponse("Chave não validada.")
    except Linha.DoesNotExist:
        return HttpResponse("Nao existe linha com esse Id")
    except KeyError:
        return HttpResponse("Chave de autenticação não fornecida ou usou método GET")
    except Exception as ex:
        return HttpResponse(ex)

@csrf_exempt
def import_lines(request):
    try:
        if request.method == 'GET':
            return HttpResponse("Não há método GET disponível nesse link, tente POST.")
        chave = request.POST['auth']
        if not Chave.objects.filter(Token=chave).exists():
            return HttpResponse("Chave não validada.")
        lines = csv.reader(decode_utf8(request.FILES['file']))
        line={}
        valid = ''
        invalid = ''
        for i in lines:
            Id=i[0]
            line['Id']=int(Id)
            line['Name']=i[1]
            line['Paradas']=[]
            for j in range(2,len(i)):
                line['Paradas'].append(int(i[j]))
            form = LinhaForm(line or None)
            if form.is_valid():
                form.save()
                valid += (Id+'\n')
            else:
                invalid += (Id+'\n')
        return HttpResponse('Adicionadas:\n'+valid[:-1]+'Inválidas:\n'+invalid[:-1],content_type='text/plain')
    except KeyError:
        return HttpResponse("Chave de autenticação arquivo não fornecidos.")
    except Exception as ex:
        return HttpResponse(ex)

@csrf_exempt
def import_lines_update(request):
    try:
        if request.method == 'GET':
            return HttpResponse("Não há método GET disponível nesse link, tente POST.")
        chave = request.POST['auth']
        if not Chave.objects.filter(Token=chave).exists():
            return HttpResponse("Chave não validada.")
        lines = csv.reader(decode_utf8(request.FILES['file']))
        line={}
        valid = ''
        invalid = ''
        for i in lines:
            Id=i[0]
            try:
                old_line = Linha.objects.get(pk=int(Id))
                line['Id']=old_line.Id
                if i[1]!='':
                    line['Name']=i[1]
                else:
                    line['Name']=old_line.Name
                line['Paradas']=[]
                for j in range(2,len(i)):
                    line['Paradas'].append(int(i[j]))
                line['Paradas']+=old_line.Paradas.all()
                form = LinhaForm(line or None,instance=old_line)
                if form.is_valid():
                    form.save()
                    valid += (Id+'\n')
                else:
                    invalid += (Id+'\n')
            except Exception as ex:
                invalid += (Id+'\n')
        return HttpResponse('Atualizadas:\n'+valid[:-1]+'Inválidas:\n'+invalid[:-1],content_type='text/plain')
    except KeyError:
        return HttpResponse("Chave de autenticação ou arquivo não fornecidos.")
    except Exception as ex:
        return HttpResponse(ex)

def list_vehicles(request):
    """Retorna uma relação Id - Name com todos os veículos no banco"""
    if request.method == 'POST':
        return HttpResponse("Não há método POST disponível nesse link, tente GET.")
    vehicles = Veiculo.objects.values_list("Id", "Name")
    retorno = 'Id - Name\n'
    for k in vehicles:
        retorno += (str(k[0])+' - '+k[1]+'\n')
    return HttpResponse(retorno, content_type='text/plain')

def show_vehicle_info(request, id):
    """Dado um Id, retorna todas as informações sobre o veículo que tenha esse Id. Se não existir veículo
    com esse Id, retorna uma mensagem de erro."""
    try:
        if request.method == 'POST':
            return HttpResponse("Não há método POST disponível nesse link, tente GET.")
        vehicle = Veiculo.objects.get(Id=id)
        info = 'Id='+str(vehicle.Id)+'\nName='+vehicle.Name+'\nModelo='+vehicle.Modelo+'\nLinhaId='+str(vehicle.LinhaId.Id)
        return HttpResponse(info, content_type='text/plain')
    except Veiculo.DoesNotExist:
        return HttpResponse("Não existe veículo com este Id.")
    except Exception as ex:
        return HttpResponse(ex)

@csrf_exempt
def new_vehicle(request):
    """"Tenta criar um novo veículo utilizando dados do corpo do POST. Se não houver todos as
    informações necessárias, retorna um erro. Se a inserção comprometer a integridade do banco
    de dados, retorna um erro. Caso contrário, adiciona o veículo no banco."""
    try:
        if request.method == 'GET':
            return HttpResponse("Não há método GET disponível nesse link, tente POST.")
        chave = request.POST['auth']
        if not Chave.objects.filter(Token=chave).exists():
            return HttpResponse("Chave não validada.")
        form = VeiculoForm(request.POST or None)
        if form.is_valid():
            form.save()
            return HttpResponse("Veículo adicionado com sucesso.")
        return HttpResponse("Parâmetros incorretos ou Id já existente, não foi possível adicionar o veículo novo.")
    except KeyError:
        return HttpResponse("Chave não fornecida.")
    except Exception as ex:
        return HttpResponse(ex) 

@csrf_exempt
def update_vehicle(request, id):
    """Tenta atualizar o veículo com o id passado utilizando parâmetros do POST. Não é necessário
    preencher todos os dados, só os que deseja atualizar. Se não houver o veículo solicitado ou se
    os novos dados comprometerem a integridade do banco, retorna um erro."""
    try:
        if request.method == 'GET':
            return HttpResponse("Não há método GET disponível nesse link, tente POST.")
        chave = request.POST['auth']
        if not Chave.objects.filter(Token=chave).exists():
            return HttpResponse("Chave não validada.")
        vehicle = Veiculo.objects.get(pk=id)
        Id = int(request.POST.get('Id', id))
        name = request.POST.get('Name', vehicle.Name)
        linhaid = request.POST.get('LinhaId', vehicle.LinhaId)
        modelo = request.POST.get('Modelo', vehicle.Modelo)
        updated_vehicle = {'Id':Id, 'Name':name, 'LinhaId':linhaid, 'Modelo':modelo}
        if Id != id:
            return HttpResponse('Não é permitido modificar o Id.')
        form = VeiculoForm(updated_vehicle or None, instance=vehicle)
        if form.is_valid():
            form.save()
            return HttpResponse("Veículo atualizado com sucesso.")
        return HttpResponse(("Valores inconsistentes, não foi possível modificar o veículo original."))
    except Veiculo.DoesNotExist as ex:
        return HttpResponse("Nao existe veiculo com esse Id")
    except KeyError:
        return HttpResponse("Chave não fornecida.")
    except Exception as ex:
        return HttpResponse(ex)

@csrf_exempt
def delete_vehicle(request, id):
    """Remove o veículo com o id informado, caso ele exista. Caso contrário, retorna um erro."""
    try:
        vehicle = Veiculo.objects.get(Id=id)
        chave = request.POST['auth']
        if Chave.objects.filter(Token=chave).exists() and request.method == 'POST':
            nome = 'Veículo '+str(vehicle.Id)+' removido com sucesso.'
            vehicle.delete()
            return HttpResponse(nome)
        return HttpResponse("Chave não validada.")
    except Veiculo.DoesNotExist:
        return HttpResponse("Nao existe veículo com esse Id")
    except KeyError:
        return HttpResponse("Chave de autenticação não fornecida ou usou método GET")
    except Exception as ex:
        return HttpResponse(ex)

@csrf_exempt
def import_vehicles(request):
    try:
        if request.method == 'GET':
            return HttpResponse("Não há método GET disponível nesse link, tente POST.")
        chave = request.POST['auth']
        if not Chave.objects.filter(Token=chave).exists():
            return HttpResponse("Chave não validada.")
        lines = csv.reader(decode_utf8(request.FILES['file']))
        vehicle={}
        valid = ''
        invalid = ''
        for i in lines:
            Id=i[0]
            vehicle['Id']=int(Id)
            vehicle['Name']=i[1]
            vehicle['Modelo']=i[2]
            vehicle['LinhaId']=int(i[3])
            form = VeiculoForm(vehicle or None)
            if form.is_valid():
                form.save()
                valid += (Id+'\n')
            else:
                invalid += (Id+'\n')
        return HttpResponse('Adicionados:\n'+valid[:-1]+'Inválidos:\n'+invalid[:-1],content_type='text/plain')
    except KeyError:
        return HttpResponse("Chave de autenticação ou arquivo não fornecidos.")
    except Exception as ex:
        return HttpResponse(ex)

@csrf_exempt
def import_vehicles_update(request):
    try:
        if request.method == 'GET':
            return HttpResponse("Não há método GET disponível nesse link, tente POST.")
        chave = request.POST['auth']
        if not Chave.objects.filter(Token=chave).exists():
            return HttpResponse("Chave não validada.")
        lines = csv.reader(decode_utf8(request.FILES['file']))
        vehicle={}
        valid = ''
        invalid = ''
        for i in lines:
            Id=i[0]
            try:
                old_vehicle = Veiculo.objects.get(pk=int(Id))
                vehicle['Id']=old_vehicle.Id
                if i[1]!='':
                    vehicle['Name']=i[1]
                else:
                    vehicle['Name']=old_vehicle.Name
                if i[2]!='':
                    vehicle['Modelo']=i[2]
                else:
                    vehicle['Modelo']=old_vehicle.Modelo
                if i[3]!='':
                    vehicle['LinhaId']=int(i[3])
                else:
                    vehicle['LinhaId']=old_vehicle.LinhaId
                form = VeiculoForm(vehicle or None,instance=old_vehicle)
                if form.is_valid():
                    form.save()
                    valid += (Id+'\n')
                else:
                    invalid += (Id+'\n')
            except:
                invalid += (Id+'\n')
        return HttpResponse('Atualizados:\n'+valid[:-1]+'Inválidos:\n'+invalid[:-1],content_type='text/plain')
    except KeyError:
        return HttpResponse("Chave de autenticação ou arquivo não fornecidos.")
    except Exception as ex:
        return HttpResponse(ex)

def list_positions(request):
    """Retorna uma relação Id - Name com todas as posições no banco"""
    if request.method == 'POST':
        return HttpResponse("Não há método POST disponível nesse link, tente GET.")
    positions = PosicaoVeiculo.objects.values_list("VeiculoId")
    retorno = 'VeiculoId\n'
    for k in positions:
        retorno += (str(k[0])+'\n')
    return HttpResponse(retorno, content_type='text/plain')

def show_position_info(request, id):
    """Dado um Id, retorna todas as informações sobre a posição que tenha esse Id. Se não existir posição
    com esse Id, retorna uma mensagem de erro."""
    try:
        if request.method == 'POST':
            return HttpResponse("Não há método POST disponível nesse link, tente GET.")
        position = PosicaoVeiculo.objects.get(pk=id)
        info ='VeiculoId='+str(position.VeiculoId.Id)+'\nLatitude='+str(position.Latitude)+'\nLongitude='+str(position.Longitude)+'\n'
        return HttpResponse(info, content_type='text/plain')
    except PosicaoVeiculo.DoesNotExist:
        return HttpResponse("Não existe posição com este Id.")
    except Exception as ex:
        return HttpResponse(ex)

@csrf_exempt
def new_position(request):
    """"Tenta criar uma nova posição utilizando dados do corpo do POST. Se não houver todos as
    informações necessárias, retorna um erro. Se a inserção comprometer a integridade do banco
    de dados, retorna um erro. Caso contrário, adiciona a posição no banco."""
    try:
        if request.method == 'GET':
            return HttpResponse("Não há método GET disponível nesse link, tente POST.")
        chave = request.POST['auth']
        if not Chave.objects.filter(Token=chave).exists():
            return HttpResponse("Chave não validada.")
        form = PosicaoForm(request.POST or None)
        if form.is_valid():
            form.save()
            return HttpResponse("Posição adicionada com sucesso.")
        return HttpResponse("Parâmetros incorretos ou Id já existente, não foi possível adicionar a posição nova.")
    except KeyError:
        return HttpResponse("Chave não fornecida.")
    except Exception as ex:
        return HttpResponse(ex) 

@csrf_exempt
def update_position(request, id):
    """Tenta atualizar a posição com o id passado utilizando parâmetros do POST. Não é necessário
    preencher todos os dados, só os que deseja atualizar. Se não houver a posição solicitada ou se
    os novos dados comprometerem a integridade do banco, retorna um erro."""
    try:
        if request.method == 'GET':
            return HttpResponse("Não há método GET disponível nesse link, tente POST.")
        chave = request.POST['auth']
        if not Chave.objects.filter(Token=chave).exists():
            return HttpResponse("Chave não validada.")
        position = PosicaoVeiculo.objects.get(pk=id)
        longitude = request.POST.get('Longitude', position.Longitude)
        latitude = request.POST.get('Latitude', position.Latitude)
        updated_position = {'Longitude':longitude, 'Latitude':latitude, 'VeiculoId':id}
        form = PosicaoForm(updated_position or None, instance=position)
        if form.is_valid():
            form.save()
            return HttpResponse("Posição atualizada com sucesso.")
        return HttpResponse(("Valores inconsistentes, não foi possível modificar a posição original."))
    except PosicaoVeiculo.DoesNotExist as ex:
        return HttpResponse("Nao existe posição com esse Id")
    except KeyError:
        return HttpResponse("Chave não fornecida.")
    except Exception as ex:
        return HttpResponse(ex)

@csrf_exempt
def delete_position(request, id):
    """Remove a posição com o id informado, caso ela exista. Caso contrário, retorna um erro."""
    try:
        position = PosicaoVeiculo.objects.get(pk=id)
        chave = request.POST['auth']
        if Chave.objects.filter(Token=chave).exists() and request.method == 'POST':
            nome = 'Posição '+str(position.id)+' removida com sucesso.'
            position.delete()
            return HttpResponse(nome)
        return HttpResponse("Chave não validada.")
    except PosicaoVeiculo.DoesNotExist:
        return HttpResponse("Nao existe posição com esse Id")
    except KeyError:
        return HttpResponse("Chave de autenticação não fornecida ou usou método GET")
    except Exception as ex:
        return HttpResponse(ex)

@csrf_exempt
def import_positions(request):
    try:
        if request.method == 'GET':
            return HttpResponse("Não há método GET disponível nesse link, tente POST.")
        chave = request.POST['auth']
        if not Chave.objects.filter(Token=chave).exists():
            return HttpResponse("Chave não validada.")
        lines = csv.reader(decode_utf8(request.FILES['file']))
        position={}
        valid = ''
        invalid = ''
        for i in lines:
            Id=i[0]
            position['VeiculoId']=int(Id)
            position['Latitude']=Decimal(i[1])
            position['Longitude']=Decimal(i[2])
            form = PosicaoForm(position or None)
            if form.is_valid():
                form.save()
                valid += (Id+'\n')
            else:
                invalid += (Id+'\n')
        return HttpResponse('Adicionadas:\n'+valid[:-1]+'Inválidas:\n'+invalid[:-1],content_type='text/plain')
    except KeyError:
        return HttpResponse("Chave de autenticação ou arquivo não fornecidos.")
    except Exception as ex:
        return HttpResponse(ex)

@csrf_exempt
def import_positions_update(request):
    try:
        if request.method == 'GET':
            return HttpResponse("Não há método GET disponível nesse link, tente POST.")
        chave = request.POST['auth']
        if not Chave.objects.filter(Token=chave).exists():
            return HttpResponse("Chave não validada.")
        lines = csv.reader(decode_utf8(request.FILES['file']))
        position={}
        valid = ''
        invalid = ''
        for i in lines:
            Id=i[0]
            try:
                old_position = PosicaoVeiculo.objects.get(pk=int(Id))
                position['VeiculoId']=int(Id)
                if i[1]!='':
                    position['Latitude']=Decimal(i[1])
                else:
                    position['Latitude']=old_position.Latitude
                if i[2]!='':
                    position['Longitude']=Decimal(i[2])
                else:
                    position['Longitude']=old_position.Longitude
                form = PosicaoForm(position or None,instance=old_position)
                if form.is_valid():
                    form.save()
                    valid += (Id+'\n')
                else:
                    invalid += (Id+'\n')
            except:
                invalid += (Id+'\n')
        return HttpResponse('Adicionadas:\n'+valid[:-1]+'Inválidas:\n'+invalid[:-1],content_type='text/plain')
    except KeyError:
        return HttpResponse("Chave de autenticação ou arquivo não fornecidos.")
    except Exception as ex:
        return HttpResponse(ex)

def nearby_stops(request):
    """Recebe lat e long como parâmetros GET e retorna uma lista contendo os ids e as distâncias
    referentes às paradas mais próximas da posição referente a lat e long que têm distância menor
    que 3km, limitado a 10 paradas. Se não houver nenhuma, retorna a parada mais próxima."""
    try:
        lat = Decimal(request.GET['lat'])
        longi = Decimal(request.GET['long'])
        all_stops = Parada.objects.all()
        nearby = []
        nearby_size = 0
        for i in all_stops:
            dist = distance(i.Latitude, lat, i.Longitude, longi)
            if nearby_size == 0:
                nearby.append([i.Id, i.Name, dist])
                nearby_size = 1
            elif nearby_size == 1 and nearby[0][2] > 3:
                if dist < nearby[0][2]:
                    del[nearby[0]]
                    nearby.append([i.Id, i.Name, dist])
            elif dist < 3:
                nearby.append([i.Id, i.Name, dist])
                nearby_size += 1
        nearby.sort(key=sort_key)
        info = 'Id - Name - Distance\n'
        if nearby_size < 10:
            for i in range(nearby_size):
                info += (str(nearby[i][0])+' - '+nearby[i][1]+' - '+str(nearby[i][2])[:7]+'\n')
            return HttpResponse(info)
        else:
            for i in range(10):
                info += (str(nearby[i][0])+' - '+nearby[i][1]+' - '+str(nearby[i][2])[:7]+'\n')
            return HttpResponse(info)
    except Exception as ex:
        return HttpResponse(ex)
