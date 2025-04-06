'''main logic of the rogue-like game.'''
import random
import types
import pyxel

# ゲームの定数
TITLE = "Pyxel Roguelike"
WIDTH = 160
HEIGHT = 120
TILE_SIZE = 8
MAP_WIDTH = 20
MAP_HEIGHT = 15
FLOOR = 0
WALL = 1
PLAYER_COLOR = 11
ENEMY_COLOR = 8
ITEM_COLOR = 10


def _main():
    # Pyxelの初期化
    pyxel.init(WIDTH, HEIGHT, title=TITLE)

    # ゲーム状態の初期化
    game_state = _reset_game(1)

    # ローカル更新関数の定義
    def update():
        nonlocal game_state
        game_state = _update(game_state)

    # ゲームループの開始
    pyxel.run(update, lambda: _draw(game_state))


# update関数の定義
def _update(game_state):
    # ゲームオーバー時の処理
    if _game_is_over(game_state):
        return _reset_game(1) if pyxel.btnp(pyxel.KEY_R) else game_state

    # プレイヤーの入力処理
    dx, dy = 0, 0
    if pyxel.btnp(pyxel.KEY_UP) or pyxel.btnp(pyxel.KEY_W):
        dy = -1
    elif pyxel.btnp(pyxel.KEY_DOWN) or pyxel.btnp(pyxel.KEY_S):
        dy = 1
    elif pyxel.btnp(pyxel.KEY_LEFT) or pyxel.btnp(pyxel.KEY_A):
        dx = -1
    elif pyxel.btnp(pyxel.KEY_RIGHT) or pyxel.btnp(pyxel.KEY_D):
        dx = 1

    # 移動がない場合は現在の状態を返す
    if dx == 0 and dy == 0:
        return game_state

    # 現在の状態を複製して新しいゲーム状態を作成
    new_state = _game_state_clone(game_state)

    player = new_state.player
    new_x = player.x + dx
    new_y = player.y + dy

    # 壁判定
    if _is_floor(new_state, new_x, new_y):
        # 敵との衝突判定
        enemy_hit = False
        for enemy in new_state.enemies:
            if enemy.x == new_x and enemy.y == new_y:
                # 敵を攻撃
                enemy.hp -= player.attack
                if enemy.hp <= 0:
                    new_state.enemies.remove(enemy)
                    player.exp += 1
                enemy_hit = True
                break

        if not enemy_hit:
            player.x = new_x
            player.y = new_y

        # アイテム取得判定
        for item in new_state.items:
            if item.x == player.x and item.y == player.y:
                # アイテムを拾う
                player.hp += 5
                new_state.items.remove(item)

        # 敵のターン処理
        new_state = _enemy_turn(new_state)

    # 終了条件
    if len(new_state.enemies) != 0:
        return new_state
    else:
        return _reset_game(new_state.level + 1)


# draw関数の定義
def _draw(game_state):
    pyxel.cls(0)

    # マップの描画
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            if game_state.map_data[y][x] == WALL:
                pyxel.rect(x * TILE_SIZE, y * TILE_SIZE,
                           TILE_SIZE, TILE_SIZE, 5)

    # アイテムの描画
    for item in game_state.items:
        pyxel.circ(item.x * TILE_SIZE + TILE_SIZE//2,
                   item.y * TILE_SIZE + TILE_SIZE//2,
                   TILE_SIZE//3, ITEM_COLOR)

    # 敵の描画
    for enemy in game_state.enemies:
        pyxel.rect(enemy.x * TILE_SIZE + 1,
                   enemy.y * TILE_SIZE + 1,
                   TILE_SIZE - 2, TILE_SIZE - 2, ENEMY_COLOR)

    # プレイヤーの描画
    player = game_state.player
    pyxel.rect(player.x * TILE_SIZE + 1,
               player.y * TILE_SIZE + 1,
               TILE_SIZE - 2, TILE_SIZE - 2, PLAYER_COLOR)

    # UI情報の描画
    pyxel.text(4, 2,
               f"HP: {player.hp} LV: {game_state.level} EXP: {player.exp}", 7)

    # ゲームオーバー画面
    if _game_is_over(game_state):
        pyxel.text(52, 50, "GAME OVER", 8)
        pyxel.text(38, 70, "PRESS R TO RESTART", 7)


def _game_state_clone(game_state):
    def clone(entity): return types.SimpleNamespace(**vars(entity))

    return types.SimpleNamespace(
        level=game_state.level,
        map_data=game_state.map_data,
        player=clone(game_state.player),
        enemies=[clone(enemy) for enemy in game_state.enemies],
        items=[clone(item) for item in game_state.items]
    )


def _game_is_over(game_state):
    return game_state.player.hp <= 0


def _reset_game(level):
    '''新しいゲーム状態を作成して返す。'''
    map_data = _generate_map()

    # プレイヤー、敵、アイテム配置のための空き場所を順不同で返すジェネレーターを作成
    def gen_free_places():
        floors = [{'x': x, 'y': y}
                  for y in range(MAP_HEIGHT)
                  for x in range(MAP_WIDTH)
                  if map_data[y][x] == FLOOR]
        random.shuffle(floors)
        yield from floors

    free_places = gen_free_places()

    # プレイヤーの初期化
    player = types.SimpleNamespace(**next(free_places), hp=20, attack=5, exp=0)

    # 敵の初期化
    enemies = [types.SimpleNamespace(**next(free_places), hp=10, attack=2)
               for _ in range(3)]  # 敵の数

    # アイテムの初期化
    items = [types.SimpleNamespace(**next(free_places))
             for _ in range(2)]  # アイテムの数

    return types.SimpleNamespace(
        level=level,
        map_data=map_data,
        player=player,
        enemies=enemies,
        items=items
    )


def _generate_map():
    # 単純なダンジョンマップの生成
    new_map = [[WALL for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]

    # 中央に部屋を作る
    for y in range(3, MAP_HEIGHT - 3):
        for x in range(3, MAP_WIDTH - 3):
            new_map[y][x] = FLOOR

    # ランダムに壁を追加して迷路風にする
    for _ in range(10):
        x = random.randint(4, MAP_WIDTH - 5)
        y = random.randint(4, MAP_HEIGHT - 5)
        new_map[y][x] = WALL

    return new_map


def _enemy_turn(game_state):
    new_state = _game_state_clone(game_state)

    # 敵の行動
    player = new_state.player
    for enemy in new_state.enemies:
        # プレイヤーへの攻撃
        if abs(enemy.x - player.x) <= 1 and abs(enemy.y - player.y) <= 1:
            if random.random() < 0.9:  # 見逃し、空振り判定。
                player.hp -= enemy.attack
        else:
            # プレイヤーに近づく簡単なAI
            dx = 1 if player.x > enemy.x else -1 if player.x < enemy.x else 0
            dy = 1 if player.y > enemy.y else -1 if player.y < enemy.y else 0

            # ランダム性を加える
            if random.random() < 0.3:
                if random.random() < 0.5:
                    dx = 0
                else:
                    dy = 0

            new_x = enemy.x + dx
            new_y = enemy.y + dy

            # 移動可能かどうかを確認
            if (_is_floor(new_state, new_x, new_y) and
                    not _is_occupied(new_state, new_x, new_y)):
                enemy.x = new_x
                enemy.y = new_y

    return new_state


def _is_floor(game_state, x, y):
    return (0 <= x < MAP_WIDTH and
            0 <= y < MAP_HEIGHT and
            game_state.map_data[y][x] == FLOOR)


def _is_occupied(game_state, x, y):
    '''指定した座標に何かエンティティがあるか確認。'''
    def entities():
        yield game_state.player
        yield from game_state.enemies
        yield from game_state.items

    return any(entity for entity in entities() if entity.x == x and entity.y == y)


if __name__ == "__main__":
    _main()
