# การดูแล skill นี้

สำหรับคนที่จะแก้ skill ไม่ใช่คนที่จะใช้งาน · ถ้าคุณแค่จะใช้ อ่าน `README.md` พอ

## โครง repo

```
skills/code-to-figma/
├── SKILL.md          ตัวหลัก ≤280 บรรทัด — intake + branching + กฎ + ชี้ไป references
├── references/       คู่มือละเอียด โหลดเฉพาะตอนที่ต้องใช้ (14 ไฟล์ รวม stacks/)
├── templates/        ไฟล์ที่ copy เข้าไป "ในโปรเจกต์ปลายทาง" ไม่ใช่เอกสารของ skill
├── scripts/          4 สคริปต์ + fixtures + selftest
└── evals/            ทดสอบ "พฤติกรรม" ของ agent ไม่ใช่ทดสอบโค้ด
skills/flutter-widgetbook-catalog/    absorbed มาแล้ว — repo นี้คือต้นฉบับหลัก
skills/flutter-catalog-page-stories/  absorbed มาแล้ว — repo นี้คือต้นฉบับหลัก
```

**templates/ กับ references/ ห้ามปนกัน** — references คือของที่ *อ่าน* · templates คือของที่
*copy ออกไป* แล้วโปรเจกต์ปลายทางเป็นเจ้าของ ถ้าเอาไปรวมกัน agent จะสับสนระหว่าง
"ไฟล์คุมงานจริงของลูกค้า" กับ "เอกสารของ skill"

## สัญญาของแต่ละสคริปต์

ทุกตัวมี `--help` และรันด้วย `python3` เฉย ๆ ไม่ต้องลง venv

| สคริปต์ | เข้า | ออก | exit code |
|---|---|---|---|
| `extract_tokens.py` | config `{family: [{glob, preset\|pattern}]}` + `--root` | `{family: {name: {value, file, line}}}` | 0 เสมอ |
| `token_diff.py` | `--code` (ผลจากตัวบน) + `--figma` (dump) | รายงานทีละค่า | **0 ต่อเมื่อตรงทุกค่า** |
| `image_diff.py` | `--ref` `--fig` `--scale` | mean / % / **แถบที่ต่าง** | 0 = รันจบ ไม่ได้แปลว่าผ่าน |
| `segment_text.py` | JSON array ทาง stdin | `{ต้นฉบับ: ที่แทรก ZWSP}` เฉพาะที่เปลี่ยน | 0 |

**`image_diff.py` จงใจไม่บอก PASS/FAIL** เพราะการตัดสินต้องดูว่าแถบที่ต่างอยู่ตรงไหน
ไม่ใช่ต่างกี่เปอร์เซ็นต์ · ถ้าเพิ่ม PASS/FAIL เข้าไป จะทำลายกฎข้อสำคัญที่สุดของทั้งงาน

**`token_diff.py` จงใจ exit non-zero เมื่อไม่ตรง** เพราะมันต้องใช้เป็น gate ใน CI ได้
และเพราะการรายงาน "ครบแล้ว" จากการนับคือ defect ที่สคริปต์นี้มีไว้กัน

## รัน selftest

```bash
./skills/code-to-figma/scripts/selftest.sh
```

33 ข้อ ไม่ต้องต่อเน็ต ไม่ต้องมี Figma ไม่ต้องมีโปรเจกต์ · **รันสองรอบ**
(สีเขียวรอบเดียวไม่นับว่าเขียว — เคยเจอมาแล้วว่า commit ที่รายงานว่าเขียว แดงสลับ)

ข้อที่จะ skip ถ้าเครื่องไม่พร้อม: segmentation (ต้องมี PyICU หรืออยู่บน macOS) และ
image diff (ต้องมี pillow + numpy)

**ทุก assertion ใน selftest ผูกกับความพลาดที่เกิดขึ้นจริง** ถ้าข้อไหนแดง ให้อ่านว่ามันอ้างถึง
เคสอะไรก่อนจะไปแก้เทสต์ · ข้อที่สำคัญที่สุด 2 ข้อ:

- **count trap** — dump ที่มีจำนวน token เท่ากันเป๊ะ แต่ค่าผิด 2 ตัว (ตัวเลข 1 + alpha หาย 1)
  ถ้าข้อนี้ผ่านแปลว่า `token_diff.py` พังในทางที่อันตรายที่สุด
- **scrim escalation** — ภาพที่มี element เลื่อนผิดตำแหน่ง แต่ซ่อนอยู่ใต้แผ่นทึบ
  ที่ threshold ปกติได้ **0.00%** ต้องมีตัวยกระดับ threshold มาจับให้เจอ

## regenerate fixtures ของภาพ

```bash
python3 skills/code-to-figma/scripts/fixtures/make_image_fixtures.py
```

สร้าง 4 คู่: เหมือนกัน / ต่างแค่แถวข้อความ / element เลื่อน / element เลื่อนใต้แผ่นทึบ
ภาพ reference เขียนเป็น @2x เพื่อให้เส้นทาง infer scale ถูกทดสอบไปด้วย

## แก้ templates

selftest ตรวจ schema ของ templates อยู่ ถ้าจะแก้ ระวัง 4 อย่างนี้ ไม่งั้นเทสต์แดง:

- JSON ทุกไฟล์ต้อง parse ได้ → **ห้ามใช้ `//` comment** ใช้ key ที่ขึ้นต้นด้วย `_` แทน
- `flow-edges` ต้องมี edge kind ครบ 6 แบบ
- `figma-node-registry` ต้องมี section ที่ ritual อ่าน ครบทุกอัน
- `acceptance-criteria` ต้องมีหัวข้อ A/B/C/D และตารางลายเซ็น

`project-profile` ต้องคง `evidence`, `absenceEvidence`, `finding` และ `scaleCalibrated: false`
ไว้ — 4 ตัวนี้คือกลไกบังคับความซื่อสัตย์ ไม่ใช่ field เฉย ๆ

## เพิ่ม stack ใหม่

เขียน `references/stacks/<ชื่อ>.md` ตามรูปแบบเดิม: token อยู่ไหน (พร้อม pattern) ·
มี catalog ไหม · จับภาพยังไงและ scale เท่าไร · trace flow จากไฟล์ไหน · อะไรที่ทำให้เซอร์ไพรส์

แล้วเพิ่ม 1 แถวในตาราง D1 ของ `references/discovery.md` และ 1 แถวใน `## References`
ของ SKILL.md

**บอกตรง ๆ ว่าระดับไหน** — พิสูจน์แล้ว / มี playbook / contract-level ยังไม่เคยรัน
การเขียนให้ดูมั่นใจกว่าความจริงคือ defect เดียวกับการรายงานตัวเลขที่ไม่ได้วัด

ถ้าจะเพิ่ม preset ให้ `extract_tokens.py` ใส่ใน dict `PRESETS` พร้อมคำอธิบาย 1 บรรทัด
แล้วเพิ่ม assertion ใน selftest

## evals

`evals/` เป็นการทดสอบ**พฤติกรรมของ agent** ไม่ใช่โค้ด · วิธีใช้: เปิดเซสชันใหม่สะอาด ๆ
รัน prompt ทั้งแบบมี skill และไม่มี แล้วเทียบว่าผลต่างกันตามที่ `expect` เขียนไว้ไหม
รายละเอียดใน `evals/README.md`

ทุก eval มาจากความพลาดจริง 1 เรื่อง — ถ้าจะเพิ่ม ให้เพิ่มตอนที่เจอความพลาดใหม่
ไม่ใช่เพิ่มเพื่อให้ครอบคลุมเฉย ๆ

## เรื่อง skill Flutter 2 ตัว

`flutter-widgetbook-catalog` และ `flutter-catalog-page-stories` เดิมอยู่กระจัดกระจายใน
`~/.claude/skills/` และใน repo poppa · **ตอนนี้ repo นี้คือต้นฉบับหลัก** ที่อื่นถือว่าเป็นสำเนา
ที่ install ออกไป

อัปเดตเครื่องตัวเองให้ตรงกับ repo:

```bash
./install.sh --global
```

`install.sh` จะ diff กับของเดิมและถามก่อนทับ ถ้าของเดิมต่าง — เผื่อกรณีมีคนแก้ในเครื่อง
แล้วยังไม่ได้ push กลับมา
