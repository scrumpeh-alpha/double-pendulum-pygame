import pygame
import pygame_gui
import time
from double_pendulum import DoublePendulum

# TODO: 
# setattr and getattr for smarter sliders

### MAIN PROGRAM ###

# SCREEN_X = 1280
# SCREEN_Y = 720
SCREEN_X = 1600
SCREEN_Y = 900
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

pendulum = DoublePendulum(
    angles=(1, 1),
    colors=(RED, BLUE),
    lengths=(150, 150),
    masses=(15, 30),
    pivot=PIVOT
)

parameters = [
    {"name": "Length 1", "value": pendulum.l1, "min": 10, "max": 500, "step": 10, "var_name": "l1"},
    {"name": "Length 2", "value": pendulum.l2, "min": 10, "max": 500, "step": 10, "var_name": "l2"},
    {"name": "Mass 1", "value": pendulum.m1, "min": 1, "max": 50, "step": 1, "var_name": "m1"},
    {"name": "Mass 2", "value": pendulum.m2, "min": 1, "max": 50, "step": 1, "var_name": "m2"},
    {"name": "Gravity", "value": pendulum.g, "min": 0, "max": 20, "step": 0.1, "var_name": "g"},
    {"name": "Trace Points", "value": pendulum.trace_capacity, "min": 10, "max": 3000, "step": 0.1, "var_name": "trace_capacity"},
]

## UI Elements ##
manager = pygame_gui.UIManager((SCREEN_X, SCREEN_Y), theme_path="theme.json")

main_ui_rect = pygame.Rect((2*SCREEN_X//3, 0), (SCREEN_X//3, SCREEN_Y))
main_ui_panel = pygame_gui.elements.UIPanel(
                main_ui_rect, 
                manager=manager,
                object_id="#parameter_panel"
                )

ui_elements = []
label_height, slider_height = 30, 40

padding_x, padding_y = main_ui_rect.w//6, (main_ui_rect.h//(len(parameters)+1) - 5)
for index, param in enumerate(parameters):
    pos_y = 50 + index * padding_y 
    param_name = param["name"].lower().replace(' ', '')
    
    label = pygame_gui.elements.UILabel(
        relative_rect=pygame.Rect((padding_x, pos_y), (0.7*(main_ui_rect.w - padding_x), label_height)),
        text=f"{param["name"]} :",
        manager=manager,
        container=main_ui_panel,
        object_id=f"#{param_name}_label",
    )

    slider = pygame_gui.elements.UIHorizontalSlider(
        relative_rect=pygame.Rect((padding_x, pos_y + 30), (main_ui_rect.w - 2*padding_x, slider_height)),
        start_value=param["value"],
        value_range=(param["min"], param["max"]),
        click_increment=(param["step"]),
        manager=manager,
        container=main_ui_panel,
        object_id=f"#{param_name}_slider"
    )

    text_line_width = 0.3*(main_ui_rect.w - padding_x)
    text_line = pygame_gui.elements.UITextEntryLine(
        relative_rect=pygame.Rect((main_ui_rect.w-padding_x-text_line_width, pos_y), (text_line_width, 30)),
        placeholder_text=str(param["var_name"]),
        initial_text=str(param["value"]),
        manager=manager,
        container=main_ui_panel,
        object_id=f"#{param_name}_input",
    )

    ui_elements.append((label, slider, text_line))

reset_button = pygame_gui.elements.UIButton(
    relative_rect=pygame.Rect((padding_x, 50 + len(parameters)*padding_y), (main_ui_rect.w//2 - padding_x, 50)),
    text="Reset",
    container=main_ui_panel,
    object_id="#reset_button",
    manager=manager
)

mouse_vel = pygame.mouse.get_rel()
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            pendulum.on_mouse_down()
        if event.type == pygame.MOUSEBUTTONUP:
            pendulum.on_mouse_up(mouse_vel)

        # UI Events #
        manager.process_events(event)

        if event.type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
            ui_object_id = event.ui_object_id.split('.')[1]
            for label, slider_elem, text_line in ui_elements:
                if ui_object_id == slider_elem.object_ids[1]:
                    text_line.set_text(str(event.value))
            ui_object_id = event.ui_object_id.split('.')[1]
            for param in parameters:
                param_name = param["name"].lower().replace(' ', '')
                if ui_object_id.startswith("#"+param_name):
                    setattr(pendulum, param["var_name"], event.value)

        if event.type == pygame_gui.UI_TEXT_ENTRY_FINISHED:
            ui_object_id = event.ui_object_id.split('.')[1]
            text_line_value = -1
            for label, slider_elem, text_line in ui_elements:
                if ui_object_id == text_line.object_ids[1]:
                    text_line_value = float(text_line.get_text())
                    associated_slider = slider_elem
                    associated_slider.set_current_value(text_line_value)
            for param in parameters:
                param_name = param["name"].lower().replace(' ', '')
                if ui_object_id.startswith("#"+param_name) and param["min"] <= text_line_value <= param["max"]:
                    setattr(pendulum, param["var_name"], text_line_value)


        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            ui_object_id = event.ui_object_id.split('.')[1]
            if reset_button.object_ids and ui_object_id == reset_button.object_ids[1]:
                pendulum.reset()

    manager.update(dt)

    screen.fill("black")

    pendulum.update_traces(screen)
    for _ in range(10):
        try:
            pendulum.rk4_step()
        except OverflowError as e:
            running = False
            print(e)
    pendulum.update(screen)
    mouse_vel = pygame.mouse.get_rel()

    if pendulum.held > 0:
        # print(mouse_vel)
        pendulum.on_mouse_down()

    manager.update(dt)

    manager.draw_ui(screen)

    pygame.display.update()
    dt = clock.tick(FPS)/1000.0
    time.sleep(0.001)

pygame.quit()
