import os
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

# --- CONFIGURAÇÃO BLINDADA ---
# Pega o caminho exato da pasta onde este arquivo está pra não dar erro de "TemplateNotFound"
pasta_atual = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__, template_folder=pasta_atual)

app.config['SECRET_KEY'] = 'segredo_top_gear_do_ti'
socketio = SocketIO(app, cors_allowed_origins="*")

# Estado do jogo
players = {}
bullets = [] # (Opcional: se quiséssemos validar balas no servidor, por enquanto só repassa)

# --- CONFIGURAÇÕES DA ARENA (5 Jogadores) ---
# Cores: Vermelho, Amarelo, Azul Neon, Verde Neon, Roxo
COLORS = [0xff0000, 0xffcc00, 0x00ccff, 0x33ff00, 0x9900ff]

# Spawns espalhados (pra ninguém nascer batendo)
SPAWNS = [
    {'x': -30, 'z': -30, 'angle': 0},    # P1: Canto sup esq
    {'x': 30, 'z': -30, 'angle': 0},     # P2: Canto sup dir
    {'x': 0, 'z': 30, 'angle': 3.14},    # P3: Baixo centro
    {'x': -40, 'z': 0, 'angle': 1.57},   # P4: Esquerda
    {'x': 40, 'z': 0, 'angle': -1.57}    # P5: Direita
]

@app.route('/')
def index():
    try:
        return render_template('game.html')
    except Exception as e:
        return f"<h1>ERRO CRÍTICO</h1><p>O Flask não achou o arquivo <b>game.html</b>.</p><p>Ele procurou aqui: {pasta_atual}</p>"

@socketio.on('connect')
def on_connect():
    print(f'Novo socket conectado: {request.sid} (Aguardando login...)')

@socketio.on('join_game')
def handle_join(data):
    player_id = request.sid
    player_name = data.get('name', 'Piloto Desconhecido').upper()
    
    # Evita duplicidade se o cara clicar 2x
    if player_id in players:
        return

    if len(players) < 5:
        player_index = len(players)
        spawn = SPAWNS[player_index]
        color = COLORS[player_index]
        
        players[player_id] = {
            'x': spawn['x'], 
            'z': spawn['z'], 
            'angle': spawn['angle'],
            'color': color,
            'name': player_name,
            'role': f'P{player_index + 1}',
            'balloonCount': 3,
            'start_index': player_index
        }
        
        print(f"-> {player_name} entrou como P{player_index + 1}")
        
        # Manda dados iniciais só pra quem entrou
        emit('init_player', {'id': player_id, 'data': players[player_id]})
        # Atualiza a lista de todos na sala
        emit('update_players', players, broadcast=True)
    else:
        emit('game_full', {'message': 'A arena está cheia (Máx 5)!'})

@socketio.on('disconnect')
def on_disconnect():
    player_id = request.sid
    if player_id in players:
        name = players[player_id]['name']
        print(f"<- {name} saiu do jogo.")
        del players[player_id]
    emit('update_players', players, broadcast=True)

@socketio.on('move')
def handle_move(data):
    player_id = request.sid
    if player_id in players:
        # Atualiza estado
        players[player_id].update(data)
        # Repassa pra todo mundo (menos pra quem enviou pra economizar banda)
        emit('player_moved', {'id': player_id, 'data': players[player_id]}, broadcast=True, include_self=False)

@socketio.on('shoot')
def handle_shoot(data):
    # O servidor apenas repassa o evento de tiro para os outros desenharem a bala
    emit('player_shot', data, broadcast=True, include_self=False)

@socketio.on('balloon_pop')
def handle_pop(data):
    victim_id = data['victimId']
    # Validação básica pra não ter balão negativo
    if victim_id in players:
        players[victim_id]['balloonCount'] = max(0, players[victim_id]['balloonCount'] - 1)
        # Se quiser logar quem acertou quem, pode mandar o shooterId no evento também
    
    emit('balloon_popped', data, broadcast=True)

@socketio.on('request_reset')
def handle_reset():
    print("!!! JOGO REINICIADO !!!")
    # Reseta todo mundo para os spawns originais
    for pid, p_data in players.items():
        idx = p_data.get('start_index', 0)
        # Fallback se o índice for maior que os spawns disponíveis (segurança)
        spawn = SPAWNS[idx] if idx < len(SPAWNS) else SPAWNS[0]
        
        players[pid].update({
            'x': spawn['x'], 
            'z': spawn['z'], 
            'angle': spawn['angle'], 
            'balloonCount': 3
        })
    
    emit('game_reset', players, broadcast=True)

if __name__ == '__main__':
    # Porta 5500 pra não brigar com outros apps
    print(f"--- SERVIDOR RODANDO ---")
    print(f"Acesse no seu PC: http://localhost:5500")
    print(f"Para jogar no celular, use o IP da sua máquina (ex: http://192.168.0.X:5500)")
    socketio.run(app, host='192.168.15.20', port=5500, debug=True)