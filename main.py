'''main logic of the rogue-like game using generators for flow control.'''
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
MESSAGE_COLOR = 7
MESSAGE_BG_COLOR = 0


def _main():
    # Pyxelの初期化
    pyxel.init(WIDTH, HEIGHT, title=TITLE)

    # ゲーム状態の初期化
    game_state = _reset_game(1)

    # ゲームフローを管理するジェネレーターを初期化
    game_flow = _game_loop(game_state)

    # ローカル更新関数の定義
    def update():
        nonlocal game_state, game_flow
        # ジェネレーターを進める
        try:
            game_state = next(game_flow)
        except StopIteration:
            # ゲームループが終了した場合、新しいループを開始
            game_state = _reset_game(1)
            game_flow = _game_loop(game_state)

    # ゲームループの開始
    pyxel.run(update, lambda: _draw(game_state))


def _game_loop(game_state):
    """ゲームのメインループをジェネレーターとして実装"""
    current_state = game_state

    # プレイヤーが生きている間、ゲームループを継続。
    while current_state.player.hp > 0:
        # プレイヤーターン
        current_state = yield from _player_turn(current_state)

        # このレベルの敵を全て倒した
        if not current_state.enemies:
            next_level = current_state.level + 1
            current_state = _reset_game(next_level)
            current_state.message = f"YOU ENTER LEVEL {next_level}!"

            # スペースキー入力待ち
            yield current_state
            while not pyxel.btnp(pyxel.KEY_SPACE):
                yield current_state
            current_state.message = ""

        else:
            # 敵のターン
            current_state = yield from _enemy_turn(current_state)

    # リスタート入力を待つ
    current_state.message = "YOU DIED..."
    yield current_state
    while not pyxel.btnp(pyxel.KEY_R):
        yield current_state
    return  # StopIterationを発生させて新しいゲームを開始


def _player_turn(game_state):
    """プレイヤーのターンを処理するジェネレーター"""
    current_state = game_state

    # 移動方向の決定
    dx, dy = 0, 0
    while dx == 0 and dy == 0:
        yield current_state
        if pyxel.btnp(pyxel.KEY_UP) or pyxel.btnp(pyxel.KEY_W):
            dy -= 1
        if pyxel.btnp(pyxel.KEY_DOWN) or pyxel.btnp(pyxel.KEY_S):
            dy += 1
        if pyxel.btnp(pyxel.KEY_LEFT) or pyxel.btnp(pyxel.KEY_A):
            dx -= 1
        if pyxel.btnp(pyxel.KEY_RIGHT) or pyxel.btnp(pyxel.KEY_D):
            dx += 1

    # 移動処理
    new_state = _game_state_clone(current_state)
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
                message = f"YOU DEAL {player.attack}pt DAMAGE"

                if enemy.hp <= 0:
                    new_state.enemies.remove(enemy)
                    player.exp += 1
                    message += " and SLAIN"

                new_state.message = f"{message}!"

                # メッセージ表示と入力待ち
                yield new_state
                while not pyxel.btnp(pyxel.KEY_SPACE):
                    yield new_state
                new_state.message = ""

                enemy_hit = True
                break

        if not enemy_hit:
            # 移動実行
            player.x = new_x
            player.y = new_y

            # アイテム取得判定
            for item in new_state.items:
                if item.x == player.x and item.y == player.y:
                    # アイテムを拾う
                    player.hp += 5
                    new_state.items.remove(item)
                    new_state.message = "YOU GET a POTION and HEAL 5pt."

                    # メッセージ表示と入力待ち
                    yield new_state
                    while not pyxel.btnp(pyxel.KEY_SPACE):
                        yield new_state
                    new_state.message = ""
                    break

    # プレイヤーターン終了
    return new_state


def _enemy_turn(game_state):
    """敵のターンを処理するジェネレーター"""
    current_state = game_state
    player = current_state.player

    # 各敵の攻撃フェーズ
    for enemy in current_state.enemies:
        # プレイヤー隣接判定（攻撃判定）
        if abs(enemy.x - player.x) <= 1 and abs(enemy.y - player.y) <= 1:
            if random.random() < 0.9:  # 攻撃成功判定
                # 攻撃処理
                new_state = _game_state_clone(current_state)
                new_state.player.hp -= enemy.attack
                new_state.message = f"YOU ARE DAMAGED by {enemy.attack}pt."

                # メッセージ表示と入力待ち
                yield new_state
                while not pyxel.btnp(pyxel.KEY_SPACE):
                    yield new_state
                new_state.message = ""

                current_state = new_state

                # プレイヤー死亡チェック
                if current_state.player.hp <= 0:
                    break
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

            # 移動可能かどうかを確認して移動
            if (_is_floor(current_state, new_x, new_y) and
                    not _is_occupied(current_state, new_x, new_y)):
                enemy.x = new_x
                enemy.y = new_y

    # 敵のターン終了
    return current_state


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

    # メッセージの描画
    if game_state.message:
        # メッセージ背景
        pyxel.rect(0, HEIGHT - 16, WIDTH, 16, MESSAGE_BG_COLOR)
        # メッセージテキスト
        pyxel.text(4, HEIGHT - 12, game_state.message, MESSAGE_COLOR)
        # 続行表示
        if "GAME OVER" not in game_state.message:
            pyxel.text(WIDTH - 32, HEIGHT - 12, "[SPACE]", MESSAGE_COLOR)

    # ゲームオーバー画面
    if game_state.player.hp <= 0:
        pyxel.rect(WIDTH//2 - 50, HEIGHT//2 - 15, 100, 30, 1)
        pyxel.text(52, 50, "GAME OVER", 8)
        pyxel.text(38, 70, "PRESS R TO RESTART", 7)


def _game_state_clone(game_state):
    def clone(entity): return types.SimpleNamespace(**vars(entity))

    return types.SimpleNamespace(
        level=game_state.level,
        map_data=game_state.map_data,
        player=clone(game_state.player),
        enemies=[clone(enemy) for enemy in game_state.enemies],
        items=[clone(item) for item in game_state.items],
        message=game_state.message
    )


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
        items=items,
        message=""  # メッセージを空文字で初期化
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
