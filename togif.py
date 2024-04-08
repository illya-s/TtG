import turtle
import tkinter

from typing import Callable, List

from pathlib import Path
import re
import os
import sys
import functools

import PIL.Image
from PIL.PngImagePlugin import PngImageFile
from PIL.ImageFile import ImageFile
from PIL import EpsImagePlugin


def init(**options):
    # download ghostscript: https://www.ghostscript.com/download/gsdnld.html
    if options.get('gs_windows_binary'):
        EpsImagePlugin.gs_windows_binary = options['gs_windows_binary']  # install ghostscript, otherwise->{OSError} Unable to locate Ghostscript on paths

    # https://anzeljg.github.io/rin2/book2/2405/docs/tkinter/cap-join-styles.html
    # change the default style of the line that made of two connected line segments
    tkinter.ROUND = tkinter.BUTT  # default is ROUND  # https://anzeljg.github.io/rin2/book2/2405/docs/tkinter/create_line.html


def make_gif(image_list: List[Path], output_path: Path, **options):
    """
    :param image_list:
    :param output_path:
    :param options:
        - fps: Frame Per Second. Duration and FPS, choose one to give.
        - duration milliseconds (= 1000/FPS )  (default is 0.1 sec)
        - loop  # int, if 0, then loop forever. Otherwise, it means the loop number.
    :return:
    """
    if not output_path.parent.exists():
        raise FileNotFoundError(output_path.parent)

    if not output_path.name.lower().endswith('.gif'):
        output_path = output_path / Path('.gif')
    image_list: List[ImageFile] = [PIL.Image.open(str(_)) for _ in image_list]
    im = image_list.pop(0)
    fps = options.get('fps', options.get('FPS', 10))
    im.save(output_path, format='gif', save_all=True, append_images=image_list,
            duration=options.get('duration', int(1000 / fps)),
            loop=options.get('loop', 0))


class GIFCreator:
    __slots__ = ['draw',
                 '__temp_dir', '__duration',
                 '__name', '__is_running', '__counter', ]

    TEMP_DIR = Path('.') / Path('__temp__for_gif')

    # The time gap that you pick image after another on the recording. i.e., If the value is low, then you can get more source image, so your GIF has higher quality.
    DURATION = 100  # millisecond.  # 1000 / FPS

    REBUILD = True

    def __init__(self, name, temp_dir: Path = None, duration: int = None, **options):
        self.__name = name
        self.__is_running = False
        self.__counter = 1

        self.__temp_dir = temp_dir if temp_dir else self.TEMP_DIR
        self.__duration = duration if duration else self.DURATION

        if not self.__temp_dir.exists():
            self.__temp_dir.mkdir(parents=True)  # True, it's ok when parents is not exists

    @property
    def name(self):
        return self.__name

    @property
    def duration(self):
        return self.__duration

    @property
    def temp_dir(self):
        if not self.__temp_dir.exists():
            raise FileNotFoundError(self.__temp_dir)
        return self.__temp_dir

    def configure(self, **options):
        gif_class_members = (_ for _ in dir(GIFCreator) if not _.startswith('_') and not callable(getattr(GIFCreator, _)))

        for name, value in options.items():
            name = name.upper()
            if name not in gif_class_members:
                raise KeyError(f"'{name}' does not belong to {GIFCreator} members.")
            correct_type = type(getattr(self, name))

            # type check
            assert isinstance(value, correct_type), TypeError(f'{name} type need {correct_type.__name__} not {type(value).__name__}')

            setattr(self, '_GIFCreator__' + name.lower(), value)

    def record(self, draw_func: Callable = None, **options):
        """

        :param draw_func:
        :param options:
                - fps
                - start_after: milliseconds. While waiting, white pictures will continuously generate to used as the heading image of GIF.
                - end_after:
        :return:
        """
        if draw_func and callable(draw_func):
            setattr(self, 'draw', draw_func)
        if not (hasattr(self, 'draw') and callable(getattr(self, 'draw'))):
            raise NotImplementedError('subclasses of GIFCreatorMixin must provide a draw() method')

        regex = re.compile(fr"""{self.name}_[0-9]{{4}}""")

        def wrap():
            self.draw()
            turtle.ontimer(self._stop, options.get('end_after', 0))

        wrap_draw = functools.wraps(self.draw)(wrap)

        try:
            # https://blog.csdn.net/lingyu_me/article/details/105400510
            turtle.reset()  # Does a turtle.clear() and then resets this turtle's state (i.e. direction, position etc.)
        except turtle.Terminator:
            turtle.reset()

        if self.REBUILD:
            for f in [_ for _ in self.temp_dir.glob(f'*.*') if _.suffix.upper().endswith(('EPS', 'PNG'))]:
                [os.remove(f) for ls in regex.findall(str(f)) if ls is not None]

        self._start()
        self._save()  # init start the recording
        turtle.ontimer(wrap_draw,
                       t=options.get('start_after', 0))  # start immediately
        turtle.done()
        print('convert_eps2image...')
        self.convert_eps2image()
        print('make_gif...')
        self.make_gif(fps=options.get('fps'))
        print(f'done:{self.name}')
        return

    def convert_eps2image(self):
        """
        image extension (PGM, PPM, GIF, PNG) is all compatible with tk.PhotoImage
        .. important:: you need to use ghostscript, see ``init()``
        """
        for eps_file in [_ for _ in self.temp_dir.glob('*.*') if _.name.startswith(self.__name) and _.suffix.upper() == '.EPS']:
            output_path = self.temp_dir / Path(eps_file.name + '.png')
            if output_path.exists():
                continue
            im: PIL.Image.Image = PIL.Image.open(str(eps_file))
            im.save(output_path, 'png')

    def make_gif(self, output_name=None, **options):
        """
        :param output_name: basename `xxx.png` or `xxx`
        :param options:
            - fps: for GIF
        :return:
        """

        if output_name is None:
            output_name = self.__name

        if not output_name.lower().endswith('.gif'):
            output_name += '.gif'

        image_list = [_ for _ in self.temp_dir.glob(f'{self.__name}*.*') if
                      (_.suffix.upper().endswith(('PGM', 'PPM', 'GIF', 'PNG')) and _.name.startswith(self.__name))
                      ]
        if not image_list:
            sys.stderr.write(f'There is no image on the directory. {self.temp_dir / Path(self.__name + "*.*")}')
            return
        output_path = Path('.') / Path(f'{output_name}')

        fps = options.get('fps', options.get('FPS'))
        if fps is None:
            fps = 1000 / self.duration
        make_gif(image_list, output_path,
                 fps=fps, loop=0)
        os.startfile('.')  # open the output folder

    def _start(self):
        self.__is_running = True

    def _stop(self):
        print(f'finished draw:{self.name}')
        self.__is_running = False
        self.__counter = 1

    def _save(self):
        if self.__is_running:
            # print(self.__counter)
            output_file: Path = self.temp_dir / Path(f'{self.__name}_{self.__counter:04d}.eps')
            if not output_file.exists():
                turtle.getcanvas().postscript(file=output_file)  # 0001.eps, 0002.eps ...
            self.__counter += 1
            turtle.ontimer(self._save, t=self.duration)  # trigger only once, so we need to set it again.
