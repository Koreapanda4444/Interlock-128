"""Record actual product commands, hashes, branches and cleanup relocations.

This is a reproducible inventory for manual review, not a taint analysis or a
constant-time proof. Its assertions check product/test isolation and evidence.
"""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import re
import subprocess


def run(command):
    result = subprocess.run([str(x) for x in command], text=True, capture_output=True,
                            timeout=30, check=False)
    if result.returncode:
        raise RuntimeError(f"{command!r} failed: {result.stdout}\n{result.stderr}")
    return result.stdout


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main(args):
    root, build = args.source.resolve(), args.commands.resolve().parent

    def normalize(text):
        return str(text).replace(str(build), "${BUILD_ROOT}").replace(str(root), "${SOURCE_ROOT}")

    commands = json.loads(args.commands.read_text(encoding="utf-8"))
    product = []
    for entry in commands:
        command = entry.get("command", " ".join(entry.get("arguments", [])))
        if "CMakeFiles/interlock.dir/" in command or "CMakeFiles/interlock.dir/" in entry.get("output", ""):
            if "INTERLOCK_TESTING" in command:
                raise AssertionError("product was compiled with private testing hooks")
            product.append({"file": normalize(entry["file"]), "command": normalize(command)})
    if len(product) != 3:
        raise AssertionError(f"expected the three product translation units, found {len(product)}")
    symbols = run([args.nm, "-g", "--defined-only", args.archive])
    if "il_test_" in symbols or "prefix_runner" in symbols:
        raise AssertionError("private testing symbols in product archive")
    for name in ("interlock_key_ctx_create", "interlock_key_ctx_free", "interlock_encrypt_block", "interlock_decrypt_block"):
        if name not in symbols:
            raise AssertionError(f"missing public function {name}")
    disassembly = normalize(run([args.objdump, "-drwC", "-Mintel", args.archive]))
    if "OPENSSL_cleanse" not in disassembly:
        raise AssertionError("no retained OPENSSL_cleanse relocation; review code generation")
    functions = []
    current = None
    member = ""
    header = re.compile(r"^([0-9a-f]+) <(.+)>:$")
    instruction = re.compile(r"^\s*([0-9a-f]+):\s+(?:[0-9a-f]{2}\s+)+\s*(\S+)\s*(.*)$")
    for line in disassembly.splitlines():
        if ":     file format" in line:
            member = line.split(":", 1)[0]
        match = header.match(line)
        if match:
            current = {"object": member, "name": match[2], "start": match[1], "instructions": 0,
                       "conditional_branches": [], "explicit_memory_operands": [], "relocations": []}
            functions.append(current)
            continue
        match = instruction.match(line)
        if not match or current is None:
            continue
        address, mnemonic, operands = match.groups()
        current["instructions"] += 1
        if (mnemonic.startswith("j") and mnemonic not in ("jmp", "jmpq")) or mnemonic.startswith("loop"):
            current["conditional_branches"].append({"address": address, "instruction": mnemonic+" "+operands})
        if "[" in operands and mnemonic != "lea" and "nop" not in mnemonic+" "+operands:
            operand = mnemonic+" "+operands.split("\t", 1)[0]
            if operand not in current["explicit_memory_operands"]:
                current["explicit_memory_operands"].append(operand)
        for target in re.findall(r"R_[A-Z0-9_]+\s+([^\s+-]+)", operands):
            if target not in current["relocations"]:
                current["relocations"].append(target)
    if not functions:
        raise AssertionError("objdump produced no decodable function inventory")
    paths = ["src/interlock.c", "src/interlock_key.c", "src/support.c", "src/internal.h", "include/interlock.h"]
    report = {
        "scope": "product inventory; manual source/assembly review required; no constant-time proof",
        "platform": platform.system()+" "+platform.machine(),
        "compiler": run([args.compiler, "--version"]).splitlines()[0],
        "compiler_target": run([args.compiler, "-dumpmachine"]).strip(),
        "objdump": run([args.objdump, "--version"]).splitlines()[0],
        "inventory_script_sha256": sha(Path(__file__).read_bytes()),
        "instrumented": any("-fsanitize=" in x["command"] for x in product),
        "source_sha256": {name: sha((root/name).read_bytes()) for name in paths},
        "archive_sha256": sha(args.archive.read_bytes()),
        "normalized_disassembly_sha256": sha(disassembly.encode()),
        "product_commands": product,
        "private_product_symbols_absent": True,
        "openssl_cleanse_relocation_retained": True,
        "functions": functions,
    }
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    args.disassembly.write_text(disassembly, encoding="utf-8")
    print(json.dumps({"status": "inventory recorded", "compiler": report["compiler"],
                      "functions": len(functions), "instrumented": report["instrumented"],
                      "archive_sha256": report["archive_sha256"], "constant_time_proven": False}, sort_keys=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source", "commands", "archive", "compiler", "nm", "objdump", "output", "disassembly"):
        parser.add_argument("--"+name, type=Path, required=True)
    main(parser.parse_args())
