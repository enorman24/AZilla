# providers/prebuilt.mk — run any existing ELF as-is (no build step).
#   make sim app=prebuilt:<label> elf=<path> simulator=verilator|vcs

ELF := $(elf)
provider-build:
	@test -n "$(ELF)" || { echo "ERROR: prebuilt requires elf=<path>"; exit 1; }
	@test -f "$(ELF)" || { echo "ERROR: ELF not found: $(ELF)"; exit 1; }
