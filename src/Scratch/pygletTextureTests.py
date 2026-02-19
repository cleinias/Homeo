import pyglet

window = pyglet.window.Window()
image = pyglet.image.Texture.create(256,128)
img1 = pyglet.image.load('/home/stefano/builds/from-upstream-sources/pyglet-1.2.2/examples/pyglet.png')
img2 = pyglet.image.load('/home/stefano/builds/from-upstream-sources/pyglet-1.2.2/examples/pyglet2.png')
image.blit_into(img1,0,0,0)
image.blit_into(img2,128,0,0)
@window.event
def on_draw():
    window.clear()
    image.blit(0,0)

pyglet.app.run()