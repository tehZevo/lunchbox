import pygame

#TODO: allow clicking launchpads
#TODO: make sure to send top/right button messages correctly

BUTTON_SIZE = 40
PAD_BORDER = 20

class VirtualLaunchpad:
    def __init__(self):
        self.buttons = [[(0, 0, 0) for _ in range(9)] for _ in range(9)]

    def set_color(self, x, y, rgb):
        self.buttons[y][x] = rgb

class Visualizer:
    def __init__(self):
        self.num_pads = 0
        pygame.init()
        pygame.display.set_caption("Lunchbox")
        self.pads = []

    def draw_button(self, x, y, pad, color):
        y = 8 - y
        #TODO: pad offset
        rect = pygame.Rect(x * BUTTON_SIZE + pad * 10 * BUTTON_SIZE, y * BUTTON_SIZE, BUTTON_SIZE, BUTTON_SIZE)
        pygame.draw.rect(self.screen, color, rect)
        pygame.draw.rect(self.screen, (40, 40, 40), rect, width=4)

    def draw(self):
        for i, pad in enumerate(self.pads):
            for x in range(9):
                for y in range(9):
                    color = pad.buttons[y][x]
                    self.draw_button(x, y, i, color)

    def step(self):
        self.screen.fill((0, 0, 0))
        # pygame.draw.rect(self.screen, (255, 0, 0), pygame.Rect(30, 30, 60, 60))
        self.draw()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit(0)
        pygame.display.update()

    def set_num_pads(self, num_pads):
        self.num_pads = num_pads
        self.screen = pygame.display.set_mode((num_pads * 10 * BUTTON_SIZE - BUTTON_SIZE, 9 * BUTTON_SIZE))
        self.pads = [VirtualLaunchpad() for _ in range(num_pads)]
