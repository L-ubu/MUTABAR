# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None
ROOT = os.path.dirname(os.path.abspath(SPEC))

a = Analysis(
    ['main.py'],
    pathex=[ROOT],
    binaries=[],
    datas=[
        ('assets', 'assets'),
        ('game', 'game'),
        ('persistence', 'persistence'),
    ],
    hiddenimports=[
        'objc',
        'AppKit',
        'Foundation',
        'rumps',
        'pygame',
        'game.screens.main_menu',
        'game.screens.battle',
        'game.screens.lootbox',
        'game.screens.settings',
        'game.screens.team_select',
        'game.screens.mutadex',
        'game.screens.wave_complete',
        'game.screens.run_over',
        'game.creatures.ascii_art',
        'game.creatures.database',
        'game.battle.engine',
        'game.progression.run_manager',
        'game.progression.unlocks',
        'game.progression.lootbox',
        'game.progression.mutabox',
        'game.progression.starters',
        'game.progression.mutagen',
        'game.progression.idle',
        'game.audio',
        'game.llm.engine',
        'game.llm.prompts',
        'game.events',
        'game.events.event_types',
        'game.events.resolver',
        'game.screens.event',
        'persistence.config',
        'persistence.database',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pytest', 'llama_cpp'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='mutabar',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='mutabar',
)

app = BUNDLE(
    coll,
    name='MUTABAR.app',
    icon='assets/icon.png',
    bundle_identifier='com.mutabar.app',
    info_plist={
        'CFBundleName': 'MUTABAR',
        'CFBundleDisplayName': 'MUTABAR',
        'CFBundleShortVersionString': '0.1.0',
        'LSUIElement': True,  # Hide from Dock (menu bar app)
        'NSHighResolutionCapable': True,
    },
)
