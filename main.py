import pyxel
import random

# ゲームの定数
TITLE = "Pyxel Roguelike"
WIDTH = 160
HEIGHT = 120
TILE_SIZE = 8
MAP_WIDTH = 16
MAP_HEIGHT = 16
FLOOR = 0
WALL = 1
PLAYER_COLOR = 11
ENEMY_COLOR = 8
ITEM_COLOR = 10

class Game:
    def __init__(self):
        # Pyxelの初期化
        pyxel.init(WIDTH, HEIGHT, title=TITLE)
        self.reset_game()
        pyxel.run(self.update, self.draw)
    
    def reset_game(self):
        # ゲーム状態の初期化
        self.game_over = False
        self.level = 1
        
        # マップ生成
        self.map = self.generate_map()
        
        # プレイヤーの初期化
        self.player = Player()
        self.place_entity(self.player)
        
        # 敵の初期化
        self.enemies = []
        for _ in range(3):  # 敵の数
            enemy = Enemy()
            self.place_entity(enemy)
            self.enemies.append(enemy)
        
        # アイテムの初期化
        self.items = []
        for _ in range(2):  # アイテムの数
            item = Item()
            self.place_entity(item)
            self.items.append(item)
    
    def generate_map(self):
        # 単純なダンジョンマップの生成
        map_data = [[WALL for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
        
        # 中央に部屋を作る
        for y in range(3, MAP_HEIGHT - 3):
            for x in range(3, MAP_WIDTH - 3):
                map_data[y][x] = FLOOR
        
        # ランダムに壁を追加して迷路風にする
        for _ in range(10):
            x = random.randint(4, MAP_WIDTH - 5)
            y = random.randint(4, MAP_HEIGHT - 5)
            map_data[y][x] = WALL
        
        return map_data
    
    def place_entity(self, entity):
        # エンティティをマップの空いている場所に配置
        while True:
            x = random.randint(3, MAP_WIDTH - 4)
            y = random.randint(3, MAP_HEIGHT - 4)
            if self.map[y][x] == FLOOR and not self.is_occupied(x, y):
                entity.x = x
                entity.y = y
                return
    
    def is_occupied(self, x, y):
        # 指定した座標に何かエンティティがあるか確認
        if hasattr(self, 'player') and self.player.x == x and self.player.y == y:
            return True
        
        if hasattr(self, 'enemies'):
            for enemy in self.enemies:
                if enemy.x == x and enemy.y == y:
                    return True
        
        if hasattr(self, 'items'):
            for item in self.items:
                if item.x == x and item.y == y:
                    return True
        
        return False
    
    def update(self):
        # ゲームオーバー時の処理
        if self.game_over:
            if pyxel.btnp(pyxel.KEY_R):
                self.reset_game()
            return
        
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
        
        # プレイヤー移動
        if dx != 0 or dy != 0:
            new_x = self.player.x + dx
            new_y = self.player.y + dy
            
            # 壁判定
            if 0 <= new_x < MAP_WIDTH and 0 <= new_y < MAP_HEIGHT and self.map[new_y][new_x] == FLOOR:
                # 敵との衝突判定
                enemy_hit = False
                for enemy in self.enemies:
                    if enemy.x == new_x and enemy.y == new_y:
                        # 敵を攻撃
                        enemy.hp -= self.player.attack
                        if enemy.hp <= 0:
                            self.enemies.remove(enemy)
                            self.player.exp += 1
                        enemy_hit = True
                        break
                
                if not enemy_hit:
                    self.player.x = new_x
                    self.player.y = new_y
                
                # アイテム取得判定
                for item in self.items[:]:
                    if item.x == self.player.x and item.y == self.player.y:
                        # アイテムを拾う
                        self.player.hp += 5
                        self.items.remove(item)
                
                # 敵のターン処理
                self.enemy_turn()
        
        # 終了条件
        if len(self.enemies) == 0:
            self.level += 1
            self.reset_game()
        
        if self.player.hp <= 0:
            self.game_over = True
    
    def enemy_turn(self):
        # 敵の行動
        for enemy in self.enemies:
            # プレイヤーに近づく簡単なAI
            dx = 1 if self.player.x > enemy.x else -1 if self.player.x < enemy.x else 0
            dy = 1 if self.player.y > enemy.y else -1 if self.player.y < enemy.y else 0
            
            # ランダム性を加える
            if random.random() < 0.3:
                if random.random() < 0.5:
                    dx = 0
                else:
                    dy = 0
            
            new_x = enemy.x + dx
            new_y = enemy.y + dy
            
            # 移動可能かどうかを確認
            if (0 <= new_x < MAP_WIDTH and 0 <= new_y < MAP_HEIGHT and 
                self.map[new_y][new_x] == FLOOR and not self.is_occupied(new_x, new_y)):
                enemy.x = new_x
                enemy.y = new_y
            
            # プレイヤーへの攻撃
            if abs(enemy.x - self.player.x) <= 1 and abs(enemy.y - self.player.y) <= 1:
                self.player.hp -= enemy.attack
    
    def draw(self):
        pyxel.cls(0)
        
        # マップの描画
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                if self.map[y][x] == WALL:
                    pyxel.rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE, 5)
        
        # アイテムの描画
        for item in self.items:
            pyxel.circ(item.x * TILE_SIZE + TILE_SIZE//2, 
                       item.y * TILE_SIZE + TILE_SIZE//2, 
                       TILE_SIZE//3, ITEM_COLOR)
        
        # 敵の描画
        for enemy in self.enemies:
            pyxel.rect(enemy.x * TILE_SIZE + 1, 
                     enemy.y * TILE_SIZE + 1, 
                     TILE_SIZE - 2, TILE_SIZE - 2, ENEMY_COLOR)
        
        # プレイヤーの描画
        pyxel.rect(self.player.x * TILE_SIZE + 1, 
                 self.player.y * TILE_SIZE + 1, 
                 TILE_SIZE - 2, TILE_SIZE - 2, PLAYER_COLOR)
        
        # UI情報の描画
        pyxel.text(4, 2, f"HP: {self.player.hp} LV: {self.level} EXP: {self.player.exp}", 7)
        
        # ゲームオーバー画面
        if self.game_over:
            pyxel.text(52, 50, "GAME OVER", 8)
            pyxel.text(38, 70, "PRESS R TO RESTART", 7)

class Entity:
    def __init__(self):
        self.x = 0
        self.y = 0

class Player(Entity):
    def __init__(self):
        super().__init__()
        self.hp = 20
        self.attack = 5
        self.exp = 0

class Enemy(Entity):
    def __init__(self):
        super().__init__()
        self.hp = 10
        self.attack = 2

class Item(Entity):
    def __init__(self):
        super().__init__()

# ゲーム開始
if __name__ == "__main__":
    Game()
