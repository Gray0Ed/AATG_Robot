import pygame
import time
M_LEFT = 1
M_RIGHT = 3

MAX_D = 10

DEFAULT_DIM = MAX_D
DEFAULT_GAMMA = 1
DEFAULT_TILE = -0.04

W_HEIGHT = 720
W_WIDTH = 960
TILE_WIDTH = W_HEIGHT / MAX_D
TILE_HEIGHT = W_HEIGHT / MAX_D
FONT_SIZE = int(10 * 20 / MAX_D)

GRID_COLOR = (0, 200, 12)

GAMMA_BUTTON_RECT = pygame.Rect(W_HEIGHT + 10, W_HEIGHT / 2, 100, 100)
SIZE_BUTTON_RECT = pygame.Rect(W_HEIGHT + 10, W_HEIGHT / 2 - 120, 100, 100)
REWARD_BUTTON_RECT = pygame.Rect(W_HEIGHT + 10, W_HEIGHT / 2 - 240, 100, 100)
ARROWS_BUTTON_RECT = pygame.Rect(W_HEIGHT + 10, W_HEIGHT / 2 - 360, 100, 100)
DISPLAY_ARROWS = False

screen = None
arrows_files = ["left.png", "up.png", "right.png", "down.png"]
SCALED_ARROWS = []
arrows = []

def change_dim(new_dim):
    global MAX_D, TILE_WIDTH, TILE_HEIGHT, tr, FONT_SIZE, SCALED_ARROWS
    MAX_D = new_dim
    TILE_WIDTH = W_HEIGHT / MAX_D
    TILE_HEIGHT = W_HEIGHT / MAX_D
    FONT_SIZE = int(10 * 20 / MAX_D)
    tr = Text()
    SCALED_ARROWS = []
    for arrow in arrows:
        SCALED_ARROWS.append(pygame.transform.scale(arrow, (int(TILE_WIDTH * 0.8),
                                                    int(TILE_HEIGHT * 0.8))))


def normal_color(clicked, mouse_over):
    d = {(False, False): (50, 50, 50),
         (False, True): (80, 80, 80),
         (True, False): (10, 10, 10),
         (True, True): (10, 10, 10)}
    return d[(clicked, mouse_over)]


def special_color(clicked, marked, terminal, mouse_over):
    if clicked:
        return (10, 10, 10)
    d = {(False, False): (70, 70, 70),
         (False, True): (20, 100, 20),
         (True, False): (100, 20, 20)}
    color = d[(marked, terminal)]

    if not clicked and mouse_over:
        color = list(color)
        color[0] *= 1.2
        color[1] *= 1.2
        color[2] *= 1.2
        color = tuple(color)
    return color


def int_or_old(s, old):
    try:
        return int(s)
    except:
        return old


def float_or_old(s, old):
    try: return float(s)
    except: return old


class Text(object):
    def __init__(self):
        pygame.font.init()
        self.font = pygame.font.SysFont('Monospace', FONT_SIZE)

    def render(self, text, pos):
        text_surface = self.font.render(text, True, (255, 255, 255))
        screen.blit(text_surface, pos)
tr = Text()


class Button(object):
    def __init__(self, rect, text, fillable, special, default):
        self.rect = rect
        self.text = text
        self.fillable = fillable
        self.mouse_over = False
        self.special = special 

        self.clicked = False
        self.content = default
        self.marked = False
        self.terminal = False
    
    def handle_event(self, event):
        """Prawda jesli zmieniona zawartosc przycisku, przycisk
           (od)zaznaczony lub (od)zaznaczony jak koncowy."""
        was_clicked = self.clicked
        ret = False
        if event.type == pygame.MOUSEMOTION:
            mpos = pygame.mouse.get_pos()
            if self.rect.collidepoint(mpos):
                self.mouse_over = True
            else:
                self.mouse_over = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mpos = pygame.mouse.get_pos()
            if self.rect.collidepoint(mpos):
                if event.button == M_LEFT:
                    if not self.fillable:
                        ret = True
                        self.clicked = not self.clicked
                    else:
                        self.clicked = True
                if self.special and event.button == M_RIGHT:
                    self.marked = not self.marked
                    self.clicked = False
                    if self.terminal and self.marked:
                        self.terminal = False
                    ret = True
            elif self.fillable:
                self.clicked = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN and self.fillable:
                self.clicked = False
            elif self.clicked and self.fillable and \
                    ((event.key >= pygame.K_0 and event.key <= pygame.K_9) or \
                    event.key == pygame.K_PERIOD or \
                    event.key == pygame.K_MINUS):
                self.content += chr(event.key)
                ret = False
            elif self.clicked and self.fillable and \
                    event.key == pygame.K_BACKSPACE and len(self.content):
                self.content = self.content[:-1]
                ret = False
            elif self.mouse_over and self.special \
                    and event.key == pygame.K_SPACE:
                self.clicked = False
                self.terminal = not self.terminal;
                if self.marked and self.terminal:
                    self.marked = False
                ret = True
        ret = ret or (was_clicked and not self.clicked and self.fillable)
        return ret

    def special_draw(self):
        color = special_color(self.clicked, self.marked, self.terminal,
                              self.mouse_over)
        screen.fill(color, self.rect)
        if not self.marked:
            tr.render(self.content, (self.rect.x, self.rect.y))

    def normal_draw(self):
        color = normal_color(self.clicked, self.mouse_over)
        screen.fill(color, self.rect)
        tr.render(self.text, (self.rect.x, self.rect.y))
        if self.fillable:
            tr.render(self.content, (self.rect.x, self.rect.y + FONT_SIZE + 2))

    def draw(self):
        if self.special:
            self.special_draw()
        else:
            self.normal_draw()


class Buttons(object):
    def __init__(self):
        self.compu = Computation()
        self.gamma = DEFAULT_GAMMA
        self.buttons = []
        self.gamma_button = self.add_button(GAMMA_BUTTON_RECT, "gamma", True, 
                                            False, str(DEFAULT_GAMMA))
        self.size_button = self.add_button(SIZE_BUTTON_RECT, "size", True, 
                                           False, str(MAX_D))
        self.reward_button = self.add_button(REWARD_BUTTON_RECT, "reward", True,
                                             False, str(DEFAULT_TILE))
        self.arrows_button = self.add_button(ARROWS_BUTTON_RECT, "arrows", False,
                                             False, "switch")
        self.create_buttons_grid()
        self.setup_initial_grid()

    def create_buttons_grid(self):
        grid = dict()
        for x in xrange(MAX_D):
            for y in xrange(MAX_D):
                b_rect = pygame.Rect(
                        x * TILE_WIDTH,
                        y * TILE_HEIGHT,
                        TILE_WIDTH, TILE_HEIGHT)
                grid[(x, y)] = self.add_button(b_rect, "", True , True, 
                                               str(DEFAULT_TILE))
        self.grid = grid

    def add_button(self, *ar, **kw):
        bu = Button(*ar, **kw)
        self.buttons.append(bu)
        return bu

    def handle_event(self, event):
        global DISPLAY_ARROWS
        for button in self.buttons:
            if button.handle_event(event):
                if button == self.gamma_button:
                    new_gamma = float_or_old(self.gamma_button.content, 
                                            self.gamma)
                    if new_gamma != self.gamma and new_gamma >= 0 and \
                            new_gamma <= 1:
                        self.gamma = new_gamma
                        self.compu.set_gamma(self.gamma)
                elif button == self.size_button:
                    new_size = int(float_or_old(self.size_button.content,
                                   MAX_D))
                    new_size = max(new_size, 6)
                    self.size_button.content = str(new_size)
                    change_dim(new_size)
                    self.__init__()
                    return
                elif button == self.reward_button:
                    new_reward = float_or_old(self.reward_button.content,
                                              DEFAULT_TILE)
                    snew_reward = str(new_reward)
                    self.reward_button.content = snew_reward

                    for x in xrange(MAX_D):
                        for y in xrange(MAX_D):
                            if not self.compu.grid[(x, y)].terminal:
                                self.grid[(x, y)].content = snew_reward
                                self.compu.grid[(x, y)].const_reward = new_reward
                elif button == self.arrows_button:
                    DISPLAY_ARROWS = not DISPLAY_ARROWS
                else:
                    p = filter(lambda p: self.grid[p] == button,
                                    self.grid)[0]
                    self.compu.set_pos(p, button.marked, button.terminal, 
                                       button.content)

    def draw(self):
        for button in self.buttons:
            button.draw()

    def setup_initial_grid(self):
        grid = self.grid
        grid[(0, 3)].marked = True
        grid[(1, 3)].marked = True
        grid[(2, 3)].marked = True
        grid[(3, 3)].marked = True
        grid[(4, 2)].marked = True
        grid[(4, 1)].marked = True
        grid[(4, 0)].marked = True
        grid[(1, 1)].marked = True
        grid[(3, 0)].terminal = True
        grid[(3, 0)].content = "1"
        grid[(3, 1)].content = "-1"
        grid[(3, 1)].terminal = True
        for p, bu in grid.iteritems():
            self.compu.set_pos(p, bu.marked, bu.terminal, bu.content)


class Tile:
    def __init__(self):
        self.passable = True
        self.terminal = False
        self.reward = DEFAULT_TILE
        self.new_reward = 0
        self.const_reward = DEFAULT_TILE


class Computation(object):
    def __init__(self):
        grid = dict()
        self.grid_dir = dict()
        for x in xrange(MAX_D):
            for y in xrange(MAX_D):
                grid[(x, y)] = Tile()
        self.grid = grid
        self.set_gamma(DEFAULT_GAMMA)

    def update(self):
        grid = self.grid 
        gamma = self.gamma
        dxy = [(-1, 0), (0, -1), (1, 0), (0, 1)]
        def passable_pos(p):
            x, y = p
            return x >= 0 and x < MAX_D and y >= 0 and y < MAX_D and \
                    grid[p].passable

        for ((x, y), tile) in grid.iteritems():
            tile.new_reward = tile.const_reward
            self.grid_dir[(x, y)] = -1
            if tile.terminal:
                tile.new_reward = tile.reward
                continue
            best = -10000
            best_dir = 0
            for i, (rdx, rdy) in enumerate(dxy):
                nrx = x + rdx
                nry = y + rdy
                nrp = (nrx, nry)
                su_reward = 0.
                j = -1 
                while j < 2:
                    dx, dy = dxy[(i + j) % 4]
                    j += 1
                    np = (x + dx, y + dy)
                    if passable_pos(np):
                        rew = grid[np].reward
                    else:
                        rew = tile.reward
                    if np == nrp:
                        su_reward += 0.8 * rew
                    else:
                        su_reward += 0.1 * rew 
                reward = gamma * su_reward
                if best < reward:
                    best_dir = i
                best = max(reward, best)

            self.grid_dir[(x, y)] = best_dir
            if best != -10000:
                tile.new_reward = best + tile.const_reward
        for tile in grid.itervalues():
            if tile.new_reward > 900:
                tile.new_reward = 900.
            elif tile.new_reward < -900:
                tile.new_reward = -900.
            tile.reward = tile.new_reward

    def draw(self):
        for x in xrange(1, MAX_D):
            pygame.draw.line(screen, GRID_COLOR, (x * TILE_WIDTH, 0),
                             (x * TILE_WIDTH, W_HEIGHT))
        for y in xrange(1, MAX_D):
            pygame.draw.line(screen, GRID_COLOR, (0, y * TILE_WIDTH),
                             (W_HEIGHT, y * TILE_WIDTH))

        for (lx, ly), tile in self.grid.iteritems():
            x = lx * TILE_WIDTH
            y = ly * TILE_WIDTH
            if tile.passable:
                if self.grid_dir[(lx, ly)] != -1 and DISPLAY_ARROWS:
                    screen.blit(SCALED_ARROWS[self.grid_dir[(lx, ly)]], (x, y))

                if not DISPLAY_ARROWS:
                    r = "{:.2f}".format(tile.reward)
                    tr.render(r, (x, y + FONT_SIZE + 3))

    def set_pos(self, p, marked, terminal, content):
        self.grid[p].terminal = terminal
        self.grid[p].passable = not marked
        self.grid[p].const_reward = float(content)
        self.grid[p].reward = float(content)
    
    def set_gamma(self, gamma):
        for tile in self.grid.itervalues():
            tile.reward = tile.const_reward
        self.gamma = gamma


class Main(object):
    def __init__(self):
        global screen
        screen = pygame.display.set_mode((W_WIDTH, W_HEIGHT))
        self.buttons = Buttons()

    def main_loop(self):
        for af in arrows_files:
            arrows.append(pygame.image.load(af))
        change_dim(MAX_D)

        running = 1
        t = time.time()
        while running:
            for x in xrange(100):
                event = pygame.event.poll()
                self.buttons.handle_event(event)
                if event.type == pygame.NOEVENT:
                    break
            t = time.time()
            screen.fill((1, 0, 0))
            self.buttons.compu.update()
            self.buttons.draw()
            self.buttons.compu.draw()
            if event.type == pygame.QUIT:
                running = 0
            pygame.display.flip()

main = Main()
main.main_loop()
