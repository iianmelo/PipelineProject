#!/usr/bin/env bash
# Compile the pipeline with Icarus Verilog and run the bundled programs.
# ModelSim is not required. The vendor altsyncram megafunction is replaced
# by sim/altsyncram.v for this flow only.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD="$ROOT/build"
mkdir -p "$BUILD"

cd "$ROOT"
python3 sim/build_programs.py

iverilog -g2012 -o "$BUILD/tb.vvp" \
  sim/altsyncram.v \
  design/adder.sv \
  design/ramOnChip32.v \
  design/ramOnChipData.v \
  design/Memoria32.sv \
  design/Memoria32Data.sv \
  design/RegPack.sv \
  design/RegFile.sv \
  design/alu.sv \
  design/ALUController.sv \
  design/BranchUnit.sv \
  design/Controller.sv \
  design/flopr.sv \
  design/ForwardingUnit.sv \
  design/HazardDetection.sv \
  design/imm_Gen.sv \
  design/mux2.sv \
  design/mux4.sv \
  design/datamemory.sv \
  design/instructionmemory.sv \
  design/Datapath.sv \
  design/RISC_V.sv \
  verif/tb_top.sv

run_one() {
  local name="$1"
  local dir="$2"
  echo "== $name =="
  (cd "$dir" && vvp -n "$BUILD/tb.vvp" "+vcd=$BUILD/${name}.vcd") | tee "$BUILD/${name}.log"
}

run_one original "$ROOT"
run_one forward_branch "$ROOT/sim/programs/forward_branch"
run_one lacunas "$ROOT/sim/programs/lacunas"

python3 "$ROOT/sim/check_logs.py"
python3 "$ROOT/sim/render_figures.py"
python3 "$ROOT/sim/draw_datapath.py"
if command -v rsvg-convert >/dev/null; then
  rsvg-convert -w 1800 "$ROOT/docs/diagrams/datapath.svg" -o "$ROOT/docs/diagrams/datapath.png"
  rsvg-convert "$ROOT/docs/diagrams/pipeline_timing.svg" -o "$ROOT/docs/diagrams/pipeline_timing.png"
fi
