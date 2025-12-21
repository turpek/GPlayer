from gplayer.input_handler import CV2KeyReader, InputHandler, HybridKeyReader

IP = InputHandler

CV2_SHORTCUTS = {
    ord('b'): 'PauseCommand',
    ord('q'): 'QuitCommand',
    ord('a'): 'RewindCommand',
    ord('d'): 'ProceesCommand',
    ord(']'): 'IncreaseSpeedCommand',
    ord('['): 'DecreaseSpeedCommand',
    ord(' '): 'PauseDelayCommand',
    ord('='): 'RestoreDelayCommand',
    ord('x'): 'RemoveFrameCommand',
    ord('u'): 'UndoFrameCommand',
    ord('n'): 'NextVideoCommand',
    ord('p'): 'PrevVideoCommand',
    ord('k'): 'NextSectionCommand',
    ord('j'): 'PrevSectionCommand',
    ord('s'): 'SplitSectionCommand',
    ord('y'): 'UndoSectionCommand',
    ord('c'): 'JoinSectionCommand',
    ord('r'): 'RemoveSectionCommand',
}

HYBRID_SHORTCUTS = {
    ord('b'): 'PauseCommand',
    ord('q'): 'QuitCommand',
    ord('a'): 'RewindCommand',
    ord('d'): 'ProceesCommand',
    ord(']'): 'IncreaseSpeedCommand',
    ord('['): 'DecreaseSpeedCommand',
    ord(' '): 'PauseDelayCommand',
    ord('='): 'RestoreDelayCommand',
    ord('x'): 'RemoveFrameCommand',
    ord('u'): 'UndoFrameCommand',
    ord('n'): 'NextVideoCommand',
    ord('p'): 'PrevVideoCommand',
    IP.SHIFT_BIT | ord('d'): 'NextSectionCommand',
    IP.SHIFT_BIT | ord('a'): 'PrevSectionCommand',
    ord('s'): 'SplitSectionCommand',
    IP.SHIFT_BIT | ord('u'): 'UndoSectionCommand',
    ord('c'): 'JoinSectionCommand',
    IP.SHIFT_BIT | ord('x'): 'RemoveSectionCommand',
}

SHORTCUTS = {
    CV2KeyReader: CV2_SHORTCUTS,
    HybridKeyReader: HYBRID_SHORTCUTS,
}

