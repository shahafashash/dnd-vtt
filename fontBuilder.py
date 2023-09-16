import pygame, json

ASCII = '!"#$%&\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~'


def get_bounding_box_top(surf):
    for y in range(surf.get_height()):
        for x in range(surf.get_width()):
            if surf.get_at((x,y))[3] != 0:
                return y


if __name__ == '__main__':
    pygame.font.init()

    font_path = r'./assets/fonts/CriticalRolePlay-7BByA.ttf'
    font_name = 'CriticalRolePlay124'
    font = pygame.font.Font(font_path, 124)

    surf = pygame.Surface((512, 512), pygame.SRCALPHA)
    height = font.render('A', True, (0,0,0)).get_height()

    top_offset = get_bounding_box_top(font.render('A', True, (0,0,0)))
    height = height - top_offset

    coords = []

    x = 0
    y = 0
    for c in ASCII:
        char = font.render(c, True, (0,0,0))
        char_surf = pygame.Surface((char.get_width(), height), pygame.SRCALPHA)
        char_surf.blit(char, (0, -top_offset))
        if x + char_surf.get_width() >= surf.get_width():
            y += height
            if y + height >= surf.get_height():
                new_surf = pygame.Surface((surf.get_width(), y + height), pygame.SRCALPHA)
                new_surf.blit(surf, (0,0))
                surf = new_surf
            x = 0
        surf.blit(char_surf, (x,y))
        coords.append(((x, y), (char_surf.get_width(), height)))
        x += char_surf.get_width()
    
    dic = {'path': f'./assets/fonts/{font_name}.png', 'coords': coords}
    json_object = json.dumps(dic, indent=4)

    with open(f'./assets/fonts/{font_name}.json', 'w') as outfile:
        outfile.write(json_object)
        
    pygame.image.save(surf, f'./assets/fonts/{font_name}.png')
    print('done')
