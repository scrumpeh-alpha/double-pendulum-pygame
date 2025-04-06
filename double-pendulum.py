import pygame
import numpy as np
from numpy import sin, cos
from numpy.typing import NDArray
import time
from collections import deque
import pygame_gui

# TODO: 
# setattr and getattr for smarter sliders

class Trace():
    def __init__(self, capacity):
        self.trace_queue = deque()
        self.capacity = capacity
        self.size = 0
        self.color = (200, 100, 0)

    def add(self, position: tuple[float, float]):
        while (self.size >= self.capacity):
            self.trace_queue.popleft()
            self.size -= 1
        self.trace_queue.append(position)
        self.size += 1

    def update_trace(self):
        # For path of circles
        for pos in self.trace_queue:
            pygame.draw.circle(screen, self.color, center=pos, radius=1)
        # For smooth lines
        # for i in range(self.size-1):
        #     pygame.draw.line(screen,
        #                      self.color, 
        #                      start_pos=self.trace_queue[i],
        #                      end_pos=self.trace_queue[i+1]
                         # )

    def clear(self):
        self.trace_queue.clear()
        self.size = 0

class DoublePendulum():
    def __init__(self, angles: tuple[float, float], colors: tuple[tuple, tuple], lengths: tuple[float, float], masses: tuple[float, float]) -> None:
        self.theta1 = angles[0]*np.pi/180
        self.theta2 = angles[1]*np.pi/180
        self.omega1 = 0
        self.omega2 = 0

        self.color1 = colors[0]
        self.color2 = colors[1]

        self.l1 = lengths[0]
        self.l2 = lengths[1]
        self.m1 = masses[0]
        self.m2 = masses[1]

        self.r1 = min(self.m1*1.5, 30)
        self.r2 = min(self.m2*1.5, 30)
        self.pos1 = (0, 0)
        self.pos2 = (0, 0)

        self.g = 9.81
        self.dt = 0.016
        self.held = 0
        self.trace = Trace(100)

    def set_m1(self, m1):
        self.m1 = m1
        self.r1 = min(self.m1*1.5, 30)

    def set_m2(self, m2):
        self.m2 = m2
        self.r2 = min(self.m2*1.5, 30)

    def __phi_1(self, theta1, theta2, omega2, omega1):
        dtheta = theta1 - theta2
        m1, m2, L1, L2 = self.m1, self.m2, self.l1, self.l2
        g = self.g
        return ( -m2*(L1*omega1**2*sin(dtheta)*cos(dtheta) + L2*omega2**2*sin(dtheta)) + g*(-(m1+m2)*sin(theta1) + m2*cos(dtheta)*sin(theta2)) ) / (m1*L1 + m2*L1*sin(dtheta)**2)

    def __phi_2(self, theta1, theta2, omega1, omega2):
        dtheta = theta1 - theta2
        m1, m2, L1, L2 = self.m1, self.m2, self.l1, self.l2
        g = self.g
        return ( (m1+m2)*L1*omega1**2*sin(dtheta) + m2*L2*omega2**2*sin(dtheta)*cos(dtheta) + (m1+m2)*g*(sin(theta1)*cos(dtheta) - sin(theta2)) ) / (m1*L2 + m2*L2*sin(dtheta)**2)

    def __rk4_step(self):
        if (self.theta1 > 1e6 or self.theta2 > 1e6):
            raise OverflowError
        k1 = self.__phi_1(self.theta1, self.theta2, self.omega2, self.omega1)
        k2 = self.__phi_1(self.theta1, self.theta2, self.omega2, self.omega1 + self.dt*k1/2)
        k3 = self.__phi_1(self.theta1, self.theta2, self.omega2, self.omega1 + self.dt*k2/2)
        k4 = self.__phi_1(self.theta1, self.theta2, self.omega2, self.omega1 + self.dt*k3)
        if k1 == np.nan or k2 == np.nan or k3 == np.nan or k4 == np.nan:
            raise OverflowError("Overflow in scalar power")
        self.omega1 += self.dt/6 * (k1 + 2*k2 + 2*k3 + k4)
        k1 = self.__phi_2(self.theta1, self.theta2, self.omega1, self.omega2)
        k2 = self.__phi_2(self.theta1, self.theta2, self.omega1, self.omega2 + self.dt*k1/2)
        k3 = self.__phi_2(self.theta1, self.theta2, self.omega1, self.omega2 + self.dt*k2/2)
        k4 = self.__phi_2(self.theta1, self.theta2, self.omega1, self.omega2 + self.dt*k3)
        if k1 == np.nan or k2 == np.nan or k3 == np.nan or k4 == np.nan:
            raise OverflowError("Overflow in scalar power")
        self.omega2 += self.dt/6 * (k1 + 2*k2 + 2*k3 + k4)
        # Overflow prevention
        # self.omega1 %= 2*np.pi
        # self.omega2 %= 2*np.pi
        self.theta1 %= 2*np.pi
        self.theta2 %= 2*np.pi
        self.theta1 += (self.omega1*self.dt)
        self.theta2 += (self.omega2*self.dt)

    def update(self):
        if self.theta1 > 1e6 or self.theta2 > 1e6:
            raise OverflowError("Overflow occured in theta values: Halting Program")
        x1 = PIVOT[0] + self.l1 * sin(self.theta1)
        y1 = PIVOT[1] + self.l1 * cos(self.theta1)
        x2 = x1 + self.l2 * sin(self.theta2)
        y2 = y1 + self.l2 * cos(self.theta2)
        self.pos1 = (x1, y1)
        self.pos2 = (x2, y2)

        self.trace.add(self.pos2)
        self.trace.update_trace()

        LINE_COLOR = (150, 150, 150)
        pygame.draw.line(screen, LINE_COLOR, PIVOT, (x1, y1))
        pygame.draw.line(screen, LINE_COLOR, (x1, y1), (x2, y2))
        pygame.draw.circle(screen, self.color1, (x1, y1), self.r1)
        pygame.draw.circle(screen, self.color2, (x2, y2), self.r2)

        if self.held > 0:
            return
        self.__rk4_step()

    def on_mouse_down(self):
        mouse_pos = pygame.mouse.get_pos()
        # print(mouse_pos)
        pygame.mouse.get_rel()      # Mouse velocity required to update velocity
        mouse_x1 = mouse_pos[0]-PIVOT[0]
        mouse_y1 = -mouse_pos[1]+PIVOT[1]
        if mouse_x1 == 0:
            mouse_x1 = 1e-9
        mouse_theta1 = np.arctan(mouse_y1/mouse_x1)
        if mouse_x1 < 0:
            mouse_theta1 += np.pi
        mouse_theta1 += np.pi/2
        mouse_x2 = mouse_pos[0]-self.pos1[0]
        mouse_y2 = -mouse_pos[1]+self.pos1[1]
        if mouse_x2 == 0:
            mouse_x2 = 1e-9
        mouse_theta2 = np.arctan(mouse_y2/mouse_x2)
        if mouse_x2 < 0:
            mouse_theta2 += np.pi
        mouse_theta2 += np.pi/2
        # print(mouse_theta)
        # print(mouse_pos[0]-PIVOT[0],-(mouse_pos[1]-PIVOT[1]))
        # if (mouse_vel[0] != 0 and mouse_vel[1] != 0):
        #     print(mouse_vel)
        # mouse_r = mouse_x1**2 + mouse_y1**2
        distance1 = (self.pos1[0] - mouse_pos[0])**2 + (self.pos1[1] - mouse_pos[1])**2
        distance2 = (self.pos2[0] - mouse_pos[0])**2 + (self.pos2[1] - mouse_pos[1])**2
        if (self.held != 2 and distance1 < self.r1**2 or self.held == 1):
            self.theta1 = mouse_theta1
            self.held = 1
            self.omega1 = 0
            self.omega2 = 0
            self.trace.clear()
        if (self.held != 1 and distance2 < self.r2**2 or self.held == 2):
            self.theta2 = mouse_theta2
            self.held = 2
            self.omega1 = 0
            self.omega2 = 0
            self.trace.clear()

    def on_mouse_up(self, mouse_vel):
        # TODO: set angular velocity according to mouse
        # mouse_vel = pygame.mouse.get_rel()
        # SPEED_FACTOR = 0.7
        # mouse_omega = np.arctan(mouse_vel[1]/(mouse_vel[0]-1e-9))
        # if self.held == 1:
        #     self.omega1 = SPEED_FACTOR*mouse_omega
        # if self.held == 2:
        #     self.omega2 = SPEED_FACTOR*mouse_omega
        self.held = 0
        

### MAIN PROGRAM ###

SCREEN_X = 1280
SCREEN_Y = 720
PIVOT = (SCREEN_X//3, SCREEN_Y//3)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

pygame.init()

screen = pygame.display.set_mode((SCREEN_X, SCREEN_Y))
pygame.display.set_caption("Double Pendulum")

running = True
clock = pygame.time.Clock()
FPS = 60
dt = clock.tick(FPS)

# TIME_STEPS_PER_RUN = 10

# UI Settings
FONT = ""

pendulum = DoublePendulum(
    angles=(1, 1),
    colors=(RED, BLUE),
    lengths=(150, 150),
    masses=(15, 30)
)

parameters = [
    {"name": "Length 1", "value": pendulum.l1, "min": 10, "max": 500, "step": 10},
    {"name": "Length 2", "value": pendulum.l2, "min": 10, "max": 500, "step": 10},
    {"name": "Mass 1", "value": pendulum.m1, "min": 1, "max": 50, "step": 1},
    {"name": "Mass 2", "value": pendulum.m2, "min": 1, "max": 50, "step": 1},
    {"name": "Gravity", "value": pendulum.g, "min": 0, "max": 20, "step": 0.1},
    {"name": "Trace Points", "value": pendulum.trace.capacity, "min": 10, "max": 500, "step": 0.1},
]


manager = pygame_gui.UIManager((SCREEN_X, SCREEN_Y), theme_path="theme.json")

main_ui_rect = pygame.Rect((2*SCREEN_X//3, 0), (SCREEN_X//3, SCREEN_Y))
main_ui_panel = pygame_gui.elements.UIPanel(
                main_ui_rect, 
                manager=manager,
                object_id="#parameter_panel"
                )

# hello_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((30, 20), (100, 50)),
#                                             text='Say Hello',
#                                             manager=manager,
#                                             container=main_ui_panel,
#                                             # anchors={'center':'center'}
#                                             )

ui_elements = []
padding_x, padding_y = main_ui_rect.w//6, 100
for index, param in enumerate(parameters):
    pos_y = 50 + index * padding_y 
    param_name = param["name"].lower().replace(' ', '')
    
    label = pygame_gui.elements.UILabel(
        relative_rect=pygame.Rect((padding_x, pos_y), (main_ui_rect.w - 2*padding_x, 30)),
        text=f"{param["name"]} : {param["value"]}",
        manager=manager,
        container=main_ui_panel,
        object_id=f"#{param_name}_label"
    )

    slider = pygame_gui.elements.UIHorizontalSlider(
        relative_rect=pygame.Rect((padding_x, pos_y + 30), (main_ui_rect.w - 2*padding_x, 30)),
        start_value=param["value"],
        value_range=(param["min"], param["max"]),
        click_increment=(param["step"]),
        manager=manager,
        container=main_ui_panel,
        object_id=f"#{param_name}_slider"
    )

    ui_elements.append((label, slider))


mouse_vel = pygame.mouse.get_rel()
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            pendulum.on_mouse_down()
        if event.type == pygame.MOUSEBUTTONUP:
            pendulum.on_mouse_up(mouse_vel)

        # UI Events
        manager.process_events(event)

        if event.type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
            ui_object_id = event.ui_object_id.split('.')[1]
            for label, slider_elem in ui_elements:
                if ui_object_id == slider_elem.object_ids[1]:
                    label_text = label.text.split(":")[0]
                    label.set_text(f"{label_text}: {event.value}")
            if ui_object_id == "#length1_slider":
                pendulum.l1 = event.value
            if ui_object_id == "#length2_slider":
                pendulum.l2 = event.value
            if ui_object_id == "#mass1_slider":
                pendulum.set_m1(event.value)
            if ui_object_id == "#mass2_slider":
                pendulum.set_m2(event.value)
            if ui_object_id == "#gravity_slider":
                pendulum.g = event.value
            if ui_object_id == "#tracepoints_slider":
                pendulum.trace.capacity = event.value


        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            pass
            # if event.ui_element == hello_button:
            #     print("Hello World")

    manager.update(dt)

    screen.fill("black")

    try:
        pendulum.update()
    except OverflowError as e:
        running = False
        print(e)
    mouse_vel = pygame.mouse.get_rel()

    if pendulum.held > 0:
        # print(mouse_vel)
        pendulum.on_mouse_down()

    manager.update(dt)

    manager.draw_ui(screen)

    pygame.display.update()
    dt = clock.tick(FPS)/1000
    # pendulum.dt = dt*10

pygame.quit()
