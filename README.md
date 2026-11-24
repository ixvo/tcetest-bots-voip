# IXVO voice and bots for Jay’s TCE2 — revision 2

Choose **bots**, **voice**, or **both**. Each patch applies independently. The patches also apply in either order on clean, pinned sources. If you used the original repository-based patch set, start revision 2 in fresh checkouts and a new game home. These are full feature patches, not incremental updates.

| Patch | Changed source | Deployment |
|---|---|---|
| bots.patch | Jay’s TCE2 server game module | Run stock ET: Legacy on the server and clients. Install the new qagame and bot phrases on the server. Keep Jay’s client modules. |
| voice.patch | ET: Legacy engine and Jay’s qagame/cgame | Use the patched dedicated server and patched engine on voice clients. Install the mod overlay on the server and each participating Linux client. |
| Both patches | Both repositories | One qagame combines the selected features. Use the voice-enabled engine and client overlay. |

Upstream bases are ET: Legacy master at 0c00b50cefdc51f627b069ecaf3d0325b351daa7 and jay1110/true-combat final at b702d12d2f9e2b52c46386320392536415dc6dbf (TCE2 1.0.4). Voice, bot behaviour and the phrase bank are adapted from Annoximeme/TrueCombat-Platinum v0.39.7-sandbox44.

## Build on Debian x86-64

Use Bash. Set MODE to one of the three choices. Both diffs have directory prefixes. Run git apply from the parent directory containing the named repositories, outside any other Git checkout. A bots-only build needs just Jay’s repository.

~~~bash
sudo apt install build-essential git cmake pkg-config python3 unzip
unzip ixvo-tce2-r2.zip
PATCHES="$PWD/ixvo-tce2-r2"
MODE=both
WORK="$HOME/tce2/ixvo-r2-$MODE"
SERVER_HOME="$HOME/.etlegacy-ixvo-r2-$MODE"
CLIENT_HOME="$HOME/.etlegacy-ixvo-r2-client"
DATA="$HOME/tce2/game"
mkdir -p "$WORK"
cd "$WORK"
~~~

Run the next block as a unit. DATA is your installed base path with etmain/, tce2/, and Jay’s tce2-1.0.4.pk3. Keep the engine and game data separate from the build directories.

~~~bash
(
  set -eu
  case "$MODE" in bots|voice|both) ;; *) echo "Choose bots, voice or both"; exit 2 ;; esac
  git clone -b final https://github.com/jay1110/true-combat.git true-combat
  git -C true-combat checkout --detach b702d12d2f9e2b52c46386320392536415dc6dbf
  if [ "$MODE" != bots ]; then
    sudo apt install autoconf automake libtool nasm zip curl wget patch libopus-dev libglu1-mesa-dev libgl-dev libsdl2-dev libvulkan-dev glslang-tools
    git clone https://github.com/etlegacy/etlegacy.git etlegacy
    git -C etlegacy checkout --detach 0c00b50cefdc51f627b069ecaf3d0325b351daa7
    git apply --check "$PATCHES/voice.patch"
    git apply "$PATCHES/voice.patch"
    git -C etlegacy submodule update --init --recursive
    (cd etlegacy && FEATURE_IXVO_VOICE=1 ./easybuild.sh build -64 -vk)
  fi
  if [ "$MODE" != voice ]; then
    git apply --check "$PATCHES/bots.patch"
    git apply "$PATCHES/bots.patch"
  fi
  cmake -S true-combat -B game-build -DCMAKE_BUILD_TYPE=Release -DFEATURE_OMNIBOT=ON -DTCE_BUILD_OMNIBOT_CORE=OFF -DBUILD_TESTING=OFF
  if [ "$MODE" = bots ]; then
    cmake --build game-build --parallel "$(nproc)" --target qagame
  else
    cmake --build game-build --parallel "$(nproc)" --target qagame cgame
  fi
  python3 "$PATCHES/stage-tce2.py" "$MODE" game-build/bin "$SERVER_HOME"
)
~~~

Stop the game instance before staging. Add the usual ET: Legacy dependencies for your chosen optional build features. Omit -vk for an OpenGL-only engine build. For voice and both, copy **the same built** tce2/z_ixvo-voice-linux64.pk3 from the staged server home into each client’s tce2/ directory. The server uses the loose qagame.mp.x86_64.so. The bot phrase file goes under tce2/bots/ on the server. Stage into a fresh home and keep older IXVO overlays out of the base path.

## Run

For a bots-only server, set DED to the path to your installed ET: Legacy dedicated executable. For voice or both, use the newly built executable.

~~~bash
DED="$WORK/etlegacy/build/etlded.x86_64"   # set to your installed etlded for MODE=bots
BOT_ARGS=()
if [ "$MODE" != voice ]; then BOT_ARGS=(+set omnibot_enable 0 +set ixvo_bots 1); fi
"$DED" +set fs_basepath "$DATA" +set fs_homepath "$SERVER_HOME" +set fs_game tce2 +set dedicated 1 +set sv_official 0 +set sv_pure 1 "${BOT_ARGS[@]}" +set g_gametype 7 +map obj_village
~~~

Gametype 7 is Bodycount. Use 5 for bomb mode. In a second terminal with the same WORK, DATA, SERVER_HOME and CLIENT_HOME definitions, connect a voice client with these commands. For bots only, connect using your normal ET: Legacy client and Jay’s TCE2 installation.

~~~bash
mkdir -p "$CLIENT_HOME/tce2"
cp "$SERVER_HOME/tce2/z_ixvo-voice-linux64.pk3" "$CLIENT_HOME/tce2/"
"$WORK/etlegacy/build/etl.x86_64" +set fs_game tce2 +set fs_basepath "$DATA" +set fs_homepath "$CLIENT_HOME" +connect 127.0.0.1:27960
~~~

On the server, run `ixvo_addbot 4 red Viper`, `ixvo_addbot 3 blue Kite`, then `ixvo_botstatus`. On Viper’s team, try `/say_team Viper follow`. On a voice-enabled client, bind two spare keys with `/bind h +voip` and `/bind n +voiplocal`. Hold H for radio or N for proximity.

## What changed in revision 2

- New server cvar **ixvo_botExplore**, default **1**. When a bot needs a patrol goal, it searches the directed waypoint graph from a nearby accessible node. It samples up to 12 distinct reachable nodes, prefers places its own team visited least recently, and reserves its choice for ten seconds to spread teammates out. Map initialization clears the history. Existing objective and carrier goals take priority. Use 0 for Jay’s original fallback goal selection.
- **ixvo_botstatus** reports each bot’s number of patrol selections and last patrol node. A value of -1 means it has not picked one. These are goal selections, not arrival counts.
- Ordered bots can acquire a visible opponent while following or regrouping and check visibility before attacking.
- Bots-only deployment keeps the phrase bank server-side. Voice-only deployment requires no bot code, bot assets or bot settings.

Learned routes from human players, persistent player habits, the full Platinum squad tactics system, and the staff bot-mind overlay are outside this revision. Tests used Linux x86-64, obj_village and generated audio. Physical microphone playback and a complete plant-to-defuse cycle remain unverified.

The full installation and cvar reference is published at https://ixvo.org/doku.php?id=tce:ixvo-tce2-backport
