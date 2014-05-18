#!/usr/bin/env python

from parameters import SharedParameters
from renderer import Renderer
from playlist import Playlist
from effects.base import RGBLayer, TechnicolorSnowstormLayer, WhiteOutLayer, ColorLayer
from gameplay import PercentageResponsiveEffectLayer

def generate_player_renderer(params, color):
    regular_play = Playlist([
        [ColorLayer(color)]
        ])

    no_headset = Playlist([
        [WhiteOutLayer()]
        ])

    all_lists = {params.PLAY_STATE: regular_play,
                params.NO_HEADSET_STATE: no_headset}
    return Renderer(all_lists, activePlaylist=params.NO_HEADSET_STATE)

