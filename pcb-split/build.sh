#!/bin/sh
# Generate, autoroute, pour, DRC and export JLCPCB fab files for both halves.
#
# Needs the KiCad 10 flatpak (org.kicad.KiCad), zip and freerouting, either as
# a jar (FREEROUTING_JAR=/path/to/freerouting-1.9.0.jar, runs on Java 17+) or
# the native CLI (FREEROUTING=/path/to/freerouting-cli, default: on PATH).
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)
PASSES=${PASSES:-100}

if [ -n "${FREEROUTING_JAR:-}" ]; then
    # 1.9.0 always opens its window, so this needs a desktop session
    fr() { java -jar "$FREEROUTING_JAR" "$@" -dct 0; }
else
    fr() { "${FREEROUTING:-freerouting-cli}" "$@"; }
fi

kicad() { cmd=$1; shift; flatpak run --filesystem="$HERE" --command="$cmd" org.kicad.KiCad "$@"; }

kicad python3 "$HERE/gen.py"

for side in left right; do
    dir=$HERE/$side
    pcb=$dir/pillz_split_$side.kicad_pcb
    out=$HERE/production/$side

    # Freerouting isn't deterministic and sometimes leaves a net unrouted, so
    # re-route from the unrouted board until DRC is clean
    cp "$pcb" "$dir/unrouted.tmp"
    tries=1
    until
        cp "$dir/unrouted.tmp" "$pcb"
        kicad python3 "$HERE/route.py" dsn "$pcb" "$dir/$side.dsn"
        fr -de "$dir/$side.dsn" -do "$dir/$side.ses" -mp "$PASSES"
        kicad python3 "$HERE/route.py" finish "$pcb" "$dir/$side.ses"
        kicad kicad-cli pcb drc --severity-error --exit-code-violations \
            -o "$dir/drc.rpt" "$pcb"
    do
        if [ "$tries" -ge "${TRIES:-5}" ]; then
            echo "$side: still failing DRC after $tries routing attempts, see $dir/drc.rpt" >&2
            exit 1
        fi
        tries=$((tries + 1))
        echo "$side: DRC failed, re-routing (attempt $tries)" >&2
    done
    rm -f "$dir/unrouted.tmp"

    rm -rf "$out" "$HERE/production/pillz_split_$side.zip"
    mkdir -p "$out"
    kicad kicad-cli pcb export gerbers \
        --layers F.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts \
        --subtract-soldermask -o "$out/" "$pcb"
    kicad kicad-cli pcb export drill --format excellon --excellon-units mm \
        --excellon-separate-th --generate-map --map-format gerberx2 -o "$out/" "$pcb"
    (cd "$out" && zip -q "$HERE/production/pillz_split_$side.zip" ./*)
    echo "$side: production/pillz_split_$side.zip"
done
