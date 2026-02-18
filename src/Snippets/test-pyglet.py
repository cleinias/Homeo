import pyglet

window = pyglet.window.Window()
image = pyglet.resource.image("Homeo-Khepera-thumbnail.png")
label = pyglet.text.Label('Hello, world',
                            font_name='Times New Roman',
                            font_size=36,
                            x=window.width//2, y=window.height//2,
                            anchor_x='center', anchor_y='center')

def example1():
    @window.event
    def on_draw():
        window.clear()
        label.draw()

def example2():
    @window.event
    def on_draw():
        window.clear()
        image. blit(0,0)
    



if __name__ == "__main__":

    example2()
    pyglet.app.run()
    
    