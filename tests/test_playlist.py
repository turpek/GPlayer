from src.playlist import Playlist
from pytest import fixture
from unittest.mock import MagicMock

import pytest

@fixture
def play():
    videos = [f'video-{x}.mp4' for x in range(1, 7)]
    playlist = Playlist(videos)
    yield playlist


def test_video_name_com_lista_vazia():
    expect = None
    play = Playlist([])
    result = play.video_name()
    assert expect == result


def test_video_name_com_1_video_na_lista():
    videos = ['video-1.mp4']
    expect = videos[0]
    play = Playlist(videos)
    result = play.video_name()
    assert expect == result

# ################# Testes para o método `next_video`

def test_next_video_lista_vazia():
    videos = []
    expect = None

    video_player = MagicMock()

    play = Playlist(videos)
    play.next_video(video_player)

    result = video_player.open.call_args.args
    assert expect in result


def test_next_video_1x_com_lista_de_tamanho_1():
    videos = ['video-1.mp4']
    expect = videos[0]

    video_player = MagicMock()

    play = Playlist(videos)
    play.next_video(video_player)

    result = video_player.open.call_args.args
    assert expect in result


def test_next_video_1x_com_lista_de_tamanho_6(play):
    expect = 'video-2.mp4'

    video_player = MagicMock()

    play.next_video(video_player)

    result = video_player.open.call_args.args
    assert expect in result


def test_next_video_5x_com_lista_de_tamanho_6(play):
    expect = 'video-6.mp4'

    video_player = MagicMock()

    [play.next_video(video_player) for _ in range(5)]

    result = video_player.open.call_args.args
    assert expect in result


# ################# Testes para o método `prev_video`

def test_prev_video_lista_vazia():
    videos = []
    expect = None

    video_player = MagicMock()

    play = Playlist(videos)
    play.prev_video(video_player)

    result = video_player.open.call_args.args
    assert expect in result

def test_prev_video_1x_com_lista_de_tamanho_1():
    videos = ['video-1.mp4']
    expect = videos[0]

    video_player = MagicMock()

    play = Playlist(videos)
    play.prev_video(video_player)

    result = video_player.open.call_args.args
    assert expect in result


def test_prev_video_1x_com_lista_de_tamanho_6(play):
    expect = 'video-1.mp4'

    video_player = MagicMock()

    # É necessario passar 1 vídeo para a frente para voltar
    play.next_video(video_player)
    play.prev_video(video_player)

    result = video_player.open.call_args.args
    assert expect in result


def test_prev_video_5x_com_lista_de_tamanho_6(play):
    expect = 'video-1.mp4'

    video_player = MagicMock()

    # É necessario passar 5x para a frente para voltar 5x
    [play.next_video(video_player) for _ in range(5)]
    [play.prev_video(video_player) for _ in range(5)]

    result = video_player.open.call_args.args
    assert expect in result
