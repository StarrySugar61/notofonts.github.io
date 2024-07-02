import json
import os

from fontTools.subset import Subsetter
from fontTools.ttLib import TTFont
from fontTools.merge import Merger, Options
from gftools.fix import rename_font

tiers = json.load(open('../fontrepos.json'))
state = json.load(open('../state.json'))
warnings = []

# IDK!
# use another style as fallback!
modulation2 = [
    ["Sans", ["Sans", "Serif"]],
    ["Serif", ["Serif", "Sans"]],
]


def megamerge_planes(newname, base_font, glyph_range, banned, modulation):
    # glyph_count = len(TTFont(base_font).getGlyphOrder())
    selected_repos = [k for k, v in tiers.items()]
    selected_repos = [k for k in selected_repos if k not in banned]
    selected_repos = sorted(selected_repos, key=lambda k: tiers[k]["tier"])
    mergelist = [base_font]
    for m in modulation:
        for repo in selected_repos:
            if "families" not in state[repo]:
                print(f"Skipping odd repo {repo} (no families)")
                continue
            selected_families = [x for x in state[repo]["families"].keys() if m in x and "UI" not in x]
            if not selected_families:
                continue
            files = state[repo]["families"][selected_families[0]]["files"]
            files = [x for x in files if "Regular.ttf" in x and "UI" not in x]
            target = None
            for file in files:
                if "/hinted/" in file:
                    target = file
                    break
            if target is None:
                for file in files:
                    if "/unhinted/" in file:
                        target = file
                        break
            if target is None:
                print(f"Couldn't find a target for {repo}")
                continue
            # target_font = TTFont("../" + target)
            # glyph_count += len(target_font.getGlyphOrder())
            # if glyph_count > 65535:
            #     warnings.append(f"Too many glyphs while building {newname}, stopped at {repo}")
            #     break
            mergelist.append("../" + target)
    print("Merging: ")
    for x in mergelist:
        print("  " + os.path.basename(x))
    merger = Merger(options=Options(drop_tables=["vmtx", "vhea", "MATH"]))
    merged = merger.merge(mergelist)
    rename_font(merged, newname)
    subsetter = Subsetter()
    subsetter.unicodes_requested = set(glyph_range).union({0x25cc})
    subsetter.subset(merged)
    merged.save(newname.replace(" ", "") + "-Regular.ttf")


for modulation in modulation2:
    banned = ["duployan", "latin-greek-cyrillic", "sign-writing", "test"]
    megamerge_planes(f"Noto {modulation[0]} Plane 0",
                     base_font=f"../fonts/Noto{modulation[0]}/googlefonts/ttf/Noto{modulation[0]}-Regular.ttf",
                     glyph_range=range(0x0, 0x10000),
                     banned=banned,
                     modulation=modulation[1],
                     )
    megamerge_planes(f"Noto {modulation[0]} Plane 1",
                     base_font=f"../fonts/Noto{modulation[0]}/googlefonts/ttf/Noto{modulation[0]}-Regular.ttf",
                     glyph_range=range(0x10000, 0x20000),
                     banned=banned,
                     modulation=modulation[1]
                     )

if warnings:
    print("\n\nWARNINGS:")
    for w in warnings:
        print(w)
else:
    print("Completed successfully")
