# Evals

ทดสอบ **พฤติกรรมของ agent** ไม่ใช่ทดสอบโค้ด (โค้ดอยู่ที่ `scripts/selftest.sh`)

ทุก eval ในนี้มาจาก **ความพลาดที่เกิดขึ้นจริง** ในงานที่ skill นี้ถอดแบบมา ช่อง
`baseline_failure` คือสิ่งที่ agent ทำจริงตอนไม่มี skill — ไม่ใช่สิ่งที่คิดว่ามันน่าจะทำพลาด

## วิธีรัน

เปิดเซสชันใหม่สะอาด ๆ สองรอบ รอบแรกไม่โหลด skill รอบสองโหลด แล้วเทียบผลกับ
`expected_behavior`

- **baseline** (ไม่มี skill) ควรออกมาแบบ `baseline_failure`
- **with skill** ควรทำครบทุกข้อใน `expected_behavior`

ถ้า baseline ผ่านอยู่แล้ว = eval ข้อนั้นไม่ได้วัดอะไร ให้ตัดทิ้งหรือทำให้ยากขึ้น
ถ้า with-skill ไม่ผ่าน = แก้ SKILL.md ไม่ใช่แก้ eval

## ผลรันครั้งล่าสุด — 2026-08-13

| eval | discriminate ไหม | สรุป |
|---|---|---|
| 01 intake | **ใช่ ชัดเจน** | baseline กระโดดเข้าแผน 6 ขั้นโดยไม่ถาม 2 คำถาม intake เลย · with-skill รัน D1–D8 พร้อม file:line, เจอ shadow **และ opacity** absent (baseline เจอแค่ shadow), ระบุกับดัก light/dark ในไฟล์เดียวพร้อม config `between` ที่ต้องใช้, ยก font gate เป็นตัวบล็อก P0 |
| 02 tokens | **ไม่** — ดู `known_weakness` ในไฟล์ | baseline ไปเจอ `token_diff.py` ที่วางอยู่ข้าง fixture แล้วรันเอง เลยจับได้เหมือนกัน · ต่างกันแค่ framing |
| 05 react | **ใช่** | baseline ตอบถูกเรื่อง source of truth (เก่งกว่าที่คาด) แต่ with-skill เพิ่ม: tailwind config **drift** จาก tokens.css, opacity absent, font stack ไม่ใช่ scalar → P0 เซ็นไม่ได้, breakpoints ต้องให้คนตัดสิน, alias chain ต้อง resolve ก่อน diff |
| 03, 04 | ยังไม่รัน | เป็น scenario เชิงบทสนทนา ไม่มีไฟล์จริงประกอบ |

**baseline ในรอบนี้ไม่สะอาด** — เซสชันมี memory ของโปรเจกต์เดิมอยู่ baseline ของ eval-01
เลยรู้เรื่อง 138/138 และสถานะ ON HOLD ทั้งที่ไม่ได้อ่าน skill · คนที่รันบนโปรเจกต์ใหม่จริง ๆ
จะไม่มีข้อมูลพวกนั้น ดังนั้นช่องว่างจริงกว้างกว่าที่วัดได้

**eval-05 ทำให้เจอบั๊กใน fixture ตัวเอง 3 จุด** (Storybook ไม่มี story เลย, tokens.css อ้าง
`Card.tsx` ที่ไม่มีจริง, class `.btn--*` ไม่มี CSS) — แก้แล้วทั้งหมด · ส่วน tailwind ที่ drift
เป็นของที่บังเอิญเกิดแต่ดี เลยเก็บไว้และเขียนกำกับว่าตั้งใจ

`eval-05` ใช้ fixture ใน `fixtures/react-mini/` — เป็นโปรเจกต์ React จำลองที่ไม่ต้อง
`npm install` เลย ตรวจจากรูปร่างไฟล์อย่างเดียว มีไว้พิสูจน์ว่า skill **ไม่ได้ผูกกับ Flutter**

## เพิ่ม eval ใหม่

เพิ่มตอนที่เจอความพลาดใหม่ ไม่ใช่เพิ่มเพื่อให้ครอบคลุม · หนึ่ง eval = หนึ่งความพลาด
ที่อธิบายได้ว่าเกิดขึ้นเมื่อไหร่และเสียอะไรไป
