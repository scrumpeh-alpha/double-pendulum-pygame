import pygame
import numpy as np
from numpy import sin, cos
from collections import deque


class Trace():
    def __init__(self, capacity: int):
        assert isinstance(capacity, int)
        self.trace_queue = deque()
        self.capacity = capacity
        self.size = 0
        self.color = (200, 100, 0)

    def add(self, position: tuple[float, float]) -> None:
        while (self.size >= self.capacity):
            self.trace_queue.popleft()
            self.size -= 1
        self.trace_queue.append(position)
        self.size += 1

    def update_trace(self, screen) -> None:
        # For path of circles
        for pos in self.trace_queue:
            pygame.draw.circle(screen, self.color, center=pos, radius=1)

    def clear(self) -> None:
        self.trace_queue.clear()
        self.size = 0


class DoublePendulum():
    def __init__(self, angles: tuple[float, float], colors: tuple[tuple, tuple], lengths: tuple[float, float], masses: tuple[float, float], pivot: tuple[float, float]) -> None:
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
        self.dt = 0.16
        self.held = 0
        self.trace_capacity = 100
        self.trace2 = Trace(self.trace_capacity)

        self.pivot = pivot
        self.initial_angles = angles
        self.initial_lengths = lengths
        self.initial_masses = masses

    def __setattr__(self, name: str, value) -> None:
        if name in ("m1", "m2"):
            object.__setattr__(self, name, value)
            object.__setattr__(self, f"r{name[1]}", min(value*1.5, 30))
        else:
            object.__setattr__(self, name, value)

    def set_m1(self, m1: float) -> None:
        self.m1 = m1
        self.r1 = min(self.m1*1.5, 30)

    def set_m2(self, m2: float) -> None:
        self.m2 = m2
        self.r2 = min(self.m2*1.5, 30)

    def __phi_1(self, theta1: float, theta2: float, omega2: float, omega1: float) -> float:
        dtheta = theta1 - theta2
        m1, m2, L1, L2 = self.m1, self.m2, self.l1, self.l2
        g = self.g
        return ( -m2*(L1*omega1**2*sin(dtheta)*cos(dtheta) + L2*omega2**2*sin(dtheta)) + g*(-(m1+m2)*sin(theta1) + m2*cos(dtheta)*sin(theta2)) ) / (m1*L1 + m2*L1*sin(dtheta)**2)

    def __phi_2(self, theta1: float, theta2: float, omega1: float, omega2: float) -> float:
        dtheta = theta1 - theta2
        m1, m2, L1, L2 = self.m1, self.m2, self.l1, self.l2
        g = self.g
        return ( (m1+m2)*L1*omega1**2*sin(dtheta) + m2*L2*omega2**2*sin(dtheta)*cos(dtheta) + (m1+m2)*g*(sin(theta1)*cos(dtheta) - sin(theta2)) ) / (m1*L2 + m2*L2*sin(dtheta)**2)

    def __rk4_step(self) -> None:
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

    def update(self, screen: pygame.Surface) -> None:
        if self.theta1 > 1e6 or self.theta2 > 1e6:
            raise OverflowError("Overflow occured in theta values")
        x1 = self.pivot[0] + self.l1 * sin(self.theta1)
        y1 = self.pivot[1] + self.l1 * cos(self.theta1)
        x2 = x1 + self.l2 * sin(self.theta2)
        y2 = y1 + self.l2 * cos(self.theta2)
        self.pos1 = (x1, y1)
        self.pos2 = (x2, y2)

        self.trace2.capacity = self.trace_capacity
        self.trace2.add(self.pos2)
        self.trace2.update_trace(screen)

        LINE_COLOR = (150, 150, 150)
        pygame.draw.line(screen, LINE_COLOR, self.pivot, (x1, y1))
        pygame.draw.line(screen, LINE_COLOR, (x1, y1), (x2, y2))
        pygame.draw.circle(screen, self.color1, (x1, y1), self.r1)
        pygame.draw.circle(screen, self.color2, (x2, y2), self.r2)

        if self.held > 0:
            return
        self.__rk4_step()

    def on_mouse_down(self) -> None:
        mouse_pos = pygame.mouse.get_pos()
        # print(mouse_pos)
        pygame.mouse.get_rel()      # Mouse velocity required to update velocity
        mouse_x1 = mouse_pos[0]-self.pivot[0]
        mouse_y1 = -mouse_pos[1]+self.pivot[1]
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
        # print(mouse_pos[0]-self.pivot[0],-(mouse_pos[1]-PIVOT[1]))
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
            self.trace2.clear()
        if (self.held != 1 and distance2 < self.r2**2 or self.held == 2):
            self.theta2 = mouse_theta2
            self.held = 2
            self.omega1 = 0
            self.omega2 = 0
            self.trace2.clear()

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

    def reset(self):
        self.theta1 = self.initial_angles[0]*np.pi/180
        self.theta2 = self.initial_angles[1]*np.pi/180
        self.omega1 = 0
        self.omega2 = 0

        # To reset parameters
        # self.l1 = self.initial_lengths[0]
        # self.l2 = self.initial_lengths[1]
        # self.m1 = self.initial_masses[0]
        # self.m2 = self.initial_masses[1]
        #
        # self.r1 = min(self.m1*1.5, 30)
        # self.r2 = min(self.m2*1.5, 30)

        self.trace2.clear()
