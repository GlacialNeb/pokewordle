import pygame
import requests
import random


# requests api for the pokewordle, this uses a regex filter to get 5 letter names only

api = "https://graphql.pokeapi.co/v1beta2" # graphql endpoint kinda saved this cuz the normal api doesn't have a regex thing
name_length = 5 # dynamic :D
min_name_length = 3
max_name_length = 12

def fetch_pokemon_list(length):
    try:
        response = requests.post(api, json={"query": f"""
        query GetPokemonList {{
            pokemonspecies(where: {{name: {{_regex: "^.{{{length}}}$"}}}}) {{
                name
            }}
        }}
        """})
        response.raise_for_status()
        data = response.json()
        print(f"retrieved {len(data['data']['pokemonspecies'])} pokemon names")
        return [pokemon["name"] for pokemon in data["data"]["pokemonspecies"]]
    except requests.exceptions.RequestException as e:
        print(f"error fetching data from the api: {e}")
        return []


# initialize pygame

pygame.init()

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("PokeWordle")
clock = pygame.time.Clock()

running = True
fetching = True
reset = False
guess = []
wins = [0 for _ in range(6)]
losses = 0
length_debounce = False

# core game stuff
class Button:
    def __init__(self, x, y, width, height, text, base_color=(100,100,100), hover_color=(150,150,150), clicked_color=(200,200,200)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = base_color
        self.hover_color = hover_color
        self.clicked_color = clicked_color
        self.clicked = False

    def draw(self, screen):
        action = False
        mouse_pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(mouse_pos):
            current_color = self.hover_color
            if pygame.mouse.get_pressed()[0] == 1 and not self.clicked:
                current_color = self.clicked_color
                action = True
        else:
            current_color = self.color
            
        if pygame.mouse.get_pressed()[0] == 0:
            self.clicked = False
        
        pygame.draw.rect(screen, current_color, self.rect)
        font = pygame.font.SysFont("arial", 24)
        text_surface = font.render(self.text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
        
        return action

guess_colors = {
    'correct': (100, 255, 100),
    'within': (255, 255, 100),
    'incorrect': (125, 125, 125)
}

def get_guess_colors(guess, answer):
    colors = [guess_colors['incorrect']] * len(guess) # kinda sets up a template
    remaining_letters = {} # uses this to keep track of how many of a letter there can be

    for index, letter in enumerate(guess): # pass thru the correct stuff first
        if letter == answer[index]:
            colors[index] = guess_colors['correct']
        else:
            remaining_letters[answer[index]] = remaining_letters.get(answer[index], 0) + 1

    for index, letter in enumerate(guess):
        if colors[index] != guess_colors['correct'] and remaining_letters.get(letter, 0) > 0:
            colors[index] = guess_colors['within']
            remaining_letters[letter] -= 1

    return colors

def wipe_game():
    global answer, guess, guesses, reset
    answer = random.choice(pokemon_list)
    guesses = []
    guess = []
    reset = False

def main():
    global name_length, length_debounce, fetching
    
    title = pygame.font.SysFont("arial", 28).render("PokeWordle", True, (255,255,255))
    title_rect = title.get_rect(center=(WIDTH // 2, 40))
    header = pygame.font.SysFont("arial", 18).render("gotta guess 'em all", True, (175,175,175))
    header_rect = header.get_rect(center=(WIDTH // 2, 70))
    stats = pygame.font.SysFont("arial", 18).render("\n".join(f"in {i} guesses: {count}" for i, count in enumerate(wins[:6], start=1)) + f"\nlosses: {losses}", True, (175,175,175))
    stats_rect = stats.get_rect(center=(WIDTH - 50, 80))
    length = pygame.font.SysFont("arial", 18).render(f"length: {name_length}", True, (175,175,175))
    length_rect = length.get_rect(center=(WIDTH // 2, 450))

    screen.blit(title, title_rect)
    screen.blit(header, header_rect)
    screen.blit(stats, stats_rect)
    screen.blit(length, length_rect)
    
    inc = Button(WIDTH // 2 + 41, 441, 18, 18, "+")
    dec = Button(WIDTH // 2 - 59, 441, 18, 18, "-")
    inc_pressed = inc.draw(screen)
    dec_pressed = dec.draw(screen)
    
    if inc_pressed or dec_pressed:
        if not length_debounce:
            length_debounce = True
            if inc_pressed and name_length < max_name_length:
                name_length += 1
            elif dec_pressed and name_length > min_name_length:
                name_length -= 1
            fetching = True
    elif length_debounce:
        length_debounce = False

    if reset:
        title = pygame.font.SysFont("arial", 18).render(f"the pokemon was {answer}", True, (175,175,175))
        title_rect = title.get_rect(center=(WIDTH // 2, 500))
        screen.blit(title, title_rect)
        reset_button = Button(WIDTH // 2 - 50, 530, 100, 40, "Play Again")
        if reset_button.draw(screen):
            wipe_game()
        
    for i in range(6):
        guess_at_index = guesses[i] if i < len(guesses) else None
        guess_colors = get_guess_colors(guess_at_index, answer) if guess_at_index else []
        for j in range(name_length):
            color = (30, 30, 30)
            letter = ""
            if guess_at_index and j < len(guess_at_index):
                letter = guess_at_index[j]
                color = guess_colors[j]
            elif i == len(guesses) and j < len(guess):
                letter = guess[j]
            x = WIDTH // 2 + (j - name_length / 2) * 55
            y = 100 + i * 55
            bound = 50
            pygame.draw.rect(screen, color, (x, y, bound, bound), 0)
            pygame.draw.rect(screen, (175,175,175), (x, y, bound, bound), 2)
            text = pygame.font.SysFont("arial", 28).render(letter.upper(), True, (255,255,255))
            text_rect = text.get_rect(center=(x + bound // 2, y + bound // 2))
            screen.blit(text, text_rect)
            
# main loop

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and not (fetching or reset):
            if event.key == pygame.K_RETURN:
                if len(guess) == name_length:
                    if "".join(guess) in pokemon_list:
                        guesses.append(guess.copy())
                        if "".join(guess) == answer:
                            reset = True
                            wins[len(guesses) - 1] += 1
                        elif len(guesses) == 6:
                            reset = True
                            losses += 1
                    guess = []
            elif event.key == pygame.K_BACKSPACE:
                if guess:
                    guess.pop()
            else:
                if len(guess) < name_length and event.unicode.isalpha():
                    guess.append(event.unicode.lower())

    screen.fill((30,30,30))

    if fetching:
        text = pygame.font.SysFont("arial", 28).render("fetching pokemon...", True, (175,175,175))
        text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40))
        screen.blit(text, text_rect)
        pokemon_list = fetch_pokemon_list(name_length)
        wipe_game()
        if len(pokemon_list) > 0:
            fetching = False
    else:
        main()

    pygame.display.flip()
    clock.tick(60)