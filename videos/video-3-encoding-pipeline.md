# Video 3 — Inside the Encoder: The Heart of ROV Streaming
## الـencoder بيضغط الفيديو إزاي، وكل قرار فيه بيأثر على الـpilot إزاي

| | |
|---|---|
| **المدة** | ≈ 13 دقيقة (حوالي 1700 كلمة كلام) |
| **الـSlides** | 20 · 23 · 24 · 25 · 26 · 27 · 29 · 28 · 30 · 35 · 42 · 43 · 78 |
| **الـDemos** | `raw_vs_compressed.sh` · `gop_view.sh` · `experiment_matrix.py` (A–E) · الـEncoding Lab app |
| **قبل التسجيل** | شغّل كل الـdemos مرة عشان الـcache · افتح الـEncoding Lab على 540p · اقرا `demos/03_encoding/encoding_lab_walkthrough.md` |

> 🎞️ = slide · 🧪 = Demo · 🎥 = شاشة/B-roll · ⏱️ = الوقت

---

## Opening ⏱️ 0:00

أهلاً بيكم، أنا يوسف عباس، وده الفيديو التالت، وأهم واحد في السلسلة: الـ**Encoding**.

في الفيديو الأول عرفنا إن الفيديو من غير compression مستحيل. وفي التاني عرفنا إن الـencoder غالباً هو الـbottleneck. النهارده حنفتحه من جوه. والهدف مش إنكم تكتبوا encoder، الهدف إنكم تفهموا **ليه كل setting بيأثر على قدرة الـpilot إنه يتحكم في الـROV**.

## Content Overview

1. ليه محتاجين encoding أصلاً؟ — دقيقة واحدة
2. الـencoder بيشتغل إزاي؟ — خمس خطوات
3. أهم تلات قرارات: الـBitrate، والـGOP، والـPreset
4. الـHardware ولا الـSoftware encoding
5. الـDemo: معمل الـencoding
6. إيه اللي ممكن يبوظ في الـROV
7. الـStreaming والـComputer Vision
8. الـEngineering mindset

يلّا بينا!

---

## 1. Why Do We Need Encoding? ⏱️ 0:40

🎞️ **Slide 20** — Compression is the core of the system

افتكروا الرقم: 1080p30 raw = **1.49 Gb/s**. الـtether بتاعنا مش حيشيل ده، ولا أي tether في الدنيا عملياً.

🧪 **Demo (30 ثانية):**

```bash
./demos/01_why_streaming/raw_vs_compressed.sh
```

🎥 اعرض الجدول اللي بيطلع: **10 ثواني** raw 4:2:0 = حوالي **933 MB**، ونفس العشر ثواني H.264 على 8 Mb/s = 10 MB، وعلى 1 Mb/s = **1.3 MB**، يعني حوالي **700 مرة أصغر**. وبعدين شغّل ملف الـ8 Mb/s وملف الـ1 Mb/s جنب بعض، وبص على التفاصيل الصغيرة والحواف اللي بتتحرك.

## 2. How Does a Video Encoder Work? ⏱️ 1:30

🎞️ **Slide 23** — The hybrid video encoder

مش حنبدأ بالمصطلحات. حنبدأ بسؤال:

> **لو فيه frame-ين ورا بعض شبه بعض تقريباً، ليه أبعت الصورة كاملة مرتين؟**

ده كل سر الـcompression. الـencoder بيشتغل في خمس خطوات:

### Step 1 — Frame Representation ⏱️ 2:00

🎞️ **Slide 24** — YUV and chroma subsampling

الصورة مش بتتخزن RGB، بتتخزن **YUV**:
- الـ**Y** = الـluma، يعني الإضاءة
- الـ**U** و**V** = الـchroma، يعني الألوان

وعين الإنسان حساسة للإضاءة أكتر بكتير من اللون، فالـencoder بيعمل **4:2:0**: بيحتفظ بالإضاءة كاملة، وبيقلل دقة اللون للربع. وكده بنوفر **50%** من الـdata قبل ما نبدأ ضغط أصلاً، ومحدش بياخد باله.

### Step 2 — Spatial Compression ⏱️ 2:40

🎞️ **Slide 25** — Spatial and temporal redundancy

الـencoder بيقسم الصورة **blocks**، وكل block بيتحول بـ**transform** شبه الـDCT من pixels لـ**frequencies**. وأغلب المعلومة المهمة بتبقى في الـlow frequencies، يعني الشكل العام. أما التفاصيل الدقيقة جداً فهي اللي في الـhigh frequencies، وهي اللي ممكن نتنازل عن جزء منها.

مش محتاجين نشتق المعادلات. المهم الفكرة: **الصورة فيها حاجات مهمة كتير وحاجات مش مهمة، والـtransform بيفصلهم عن بعض.**

### Step 3 — Temporal Compression ⏱️ 3:20

🎞️ **Slide 26** — I-frames, P-frames, B-frames and the GOP

هنا السحر الحقيقي. بدل ما نبعت كل frame لوحده، الـencoder بـ**يتوقع** الـframe من الـframes اللي قبله وبيبعت **الفرق** بس:

- الـ**I-frame**: صورة كاملة مستقلة، وهي **أكبر** frame.
- الـ**P-frame**: متوقَّع من frames **قبله**.
- الـ**B-frame**: متوقَّع من frames **قبله وبعده**.

ومن هنا نسأل: لو الـB-frame محتاج frame **جاي في المستقبل**، يبقى الـencoder لازم **يستنى** لحد ما المستقبل يوصل. ودي **latency** زيادة. عشان كده في الـpiloting بنقفل الـB-frames.

🧪 **Demo (40 ثانية):**

```bash
./demos/03_encoding/gop_view.sh
```

🎥 الـoutput بيوري الـpattern: الـx264 الـdefault بيطلع `IPPBBPPBPPB…`، والـlow-latency بيطلع `IPPPPPPP…` من غير ولا B. والـI-frame باين إنه spike كبير جداً، وده الـspike اللي الـtether لازم يستحمله.

### Step 4 — Quantization ⏱️ 4:20

🎞️ **Slide 27** — Quality-based vs bitrate-based encoding

دي الخطوة اللي **بنرمي فيها معلومات** بجد، وهي اللي بنتحكم فيها:

- **Quantization ضعيف** → تفاصيل أكتر → bitrate أعلى
- **Quantization قوي** → تفاصيل أقل → bitrate أقل → blocks وblur

وده الـtrade-off الأساسي بين الـcompression ratio والـdistortion.

### Step 5 — Entropy Coding ⏱️ 4:50

وفي الآخر، الأرقام اللي فاضلة بتتضغط **lossless** بطرق ذكية زي الـ**CABAC** في H.264 وH.265: الحاجة اللي بتتكرر كتير تاخد bits أقل.

> الخلاصة: الـencoder مش بيصغّر الصورة وخلاص. ده بيستغل الـredundancy، وبياخد قرارات ذكية: **أنهي معلومة تستاهل bits وأنهي لأ.**

## 3. The Three Most Important Decisions ⏱️ 5:20

🎞️ **Slide 29** — Encoder parameters: what each knob does

| القرار | بيتحكم في إيه | الـtrade-off |
|---|---|---|
| **Bitrate / Rate control** | كمية الـdata المبعوتة | Quality ↔ Bandwidth |
| **GOP / Keyframe interval** | كل قد إيه بنبعت I-frame | Compression efficiency ↔ Recovery |
| **Preset** | الـencoder بيتعب قد إيه | Speed ↔ Compression efficiency |

### الـCBR والـVBR (أو الـCRF)

- الـ**CBR** أو الـbitrate cap: bitrate ثابت ومتوقع، وده مناسب للـtether اللي سعته محدودة. بس لما المشهد يبقى صعب، الـquality هي اللي بتقع.
- الـ**VBR / CRF**: بيدي كل مشهد اللي محتاجه، فالجودة أحسن بنفس متوسط الـbitrate، بس فيه **peaks**.

ومفيش واحد فيهم أحسن على طول الخط. الـrate controller المظبوط، ومعاه **headroom** كفاية في الـnetwork، أهم من الاسم.

### الـGOP

🎞️ **Slide 30** — Packet loss: why GOP length matters

الـGOP الطويل بيوفر bits. بس لو packet ضاع، الصورة بتفضل **بايظة لحد الـI-frame الجاي**. يعني GOP 5 ثواني = ممكن 5 ثواني صورة بايظة قدام الـpilot. وكمان لما نبدّل بين الكاميرات، مش حنشوف صورة غير لما يوصل I-frame.

### الـPreset

الـpreset الأبطأ بيوفر شوية bits، بس بياكل CPU أكتر بكتير، وساعات بيزوّد الـlatency. وعلى SBC من غير hardware encoder، إحنا عايشين في ناحية الـpresets السريعة: `ultrafast` أو `veryfast`، ومعاهم `-tune zerolatency`.

🎞️ **Slide 28** — Choosing a codec

وبالنسبة للـcodec: الـH.264 لسه الـdefault الآمن، لأن أي browser وأي hardware decoder بيشغله. الـH.265 والـAV1 بيوفروا bits، بس محتاجين CPU أكتر و support في الـdecoder. وبنقارنهم **بنفس الجودة**، مش بنفس رقم الـsetting.

## 4. Hardware vs Software Encoding ⏱️ 7:40

🎞️ **Slide 35** — Where should the encoding happen?

- الـ**Software**: على الـCPU، ومرن، بس تكلفته بتكبر مع الـresolution والـFPS وعدد الـstreams، وبيسخّن.
- الـ**Hardware**: silicon مخصوص، وCPU قليل، وأداء real-time متوقع، بس الـfeatures والـcodecs محدودة باللي الـchip بيدعمه.

وحاجة مهمة: **الـhardware encoding مش معناه zero latency ولا جودة أحسن أوتوماتيك**. الـconfiguration والـpipeline اللي حواليه بيفرقوا جداً.

وترتيب التفضيل عندنا، بعد ما نقيس: **الكاميرا تعمل encode ← hardware على الـSBC ← software على الـSBC**. والـencoding على الـlaptop فوق ما بيوفرش أي bandwidth في الـtether.

## 5. Demo 3 — The Encoding Laboratory ⏱️ 8:20

ده أهم demo في السلسلة كلها.

🧪 **Demo أ: الـexperiment matrix (45 ثانية)**

```bash
python3 demos/03_encoding/experiment_matrix.py --input rov_dive.mp4
```

🎥 بيعمل encode لنفس الـclip خمس مرات، بالـrecipe بتاع الـlow latency (`ultrafast`، `zerolatency`، ومن غير B-frames):

| Exp | Bitrate | FPS | GOP |
|---|---|---|---|
| A | 8 Mbps | 30 | 30 |
| B | 4 Mbps | 30 | 30 |
| C | 2 Mbps | 30 | 30 |
| D | 2 Mbps | 60 | 60 |
| E | 2 Mbps | 30 | 120 |

وبيطلع الـsize والـbitrate الفعلي والـencoding time والـCPU والـPSNR والـSSIM. أشّر على:

- **A ← B ← C**: لما الـbitrate بيتقسم على 2، الجودة بتقع أقل بكتير من المتوقع في الأول.
- **C قصاد D**: نفس الـ2 Mbps على frames أكتر بالضعف، يعني كل frame بياخد نص الـbits، والجودة أقل والشغل أكتر. **الـFPS العالي مش ببلاش.**
- **C قصاد E**: هل الـGOP الطويل جاب جودة أحسن بنفس الـbitrate؟ في الـclip بتاعنا **لأ** تقريباً (43.2 قصاد 43.6 dB)، بس تمنه إن الصورة ممكن تفضل بايظة لحد 4 ثواني بعد أي packet loss.

🧪 **Demo ب: الـEncoding Lab app (90 ثانية)**

```bash
cd encoding_lab && streamlit run app.py
```

🎥 امشي على الخطوات اللي في `encoding_lab_walkthrough.md`:
1. **Encode**، CRF 23: الـbaseline
2. **Diff ×8**: "المناطق المنورة هي اللي الـencoder رمى منها معلومات"
3. **Bitrate cap** على 1 وبعدين 0.25 Mb/s: "الجودة بتقع بالراحة، وبعدين فجأة. دوّروا على الـknee"
4. **Bitrate over time**: الـI-frames الحمرا هي الـspikes
5. **Low latency**: الـB-frames الرمادي بيختفوا
6. **Packet loss**: GOP 1s قصاد 5s قصاد intra refresh. نفس الـloss، وواحد بيتصلح في ثانية، والتاني بيفضل بايظ 5 ثواني

## 6. What Can Go Wrong in an ROV? ⏱️ 10:40

🎞️ **Slide 42** — Camera selection & adaptive streaming

| اللي بيحصل | السبب المحتمل | الحل الهندسي |
|---|---|---|
| الفيديو بيـfreeze | انقطاع في الـnetwork أو الـdecoder وقف | Recovery و reconnect logic |
| الفيديو pixelated | الـbitrate مش كفاية | نظبط الـrate control |
| الفيديو متأخر | buffering زيادة أو encoder latency | نقلل الـlatency في الـpipeline |
| الـFPS بيقع | الـencoder أو الـprocessing مضغوط | نقلل الـworkload |
| الصورة بتبوظ بعد packet loss | reference data ضاعت | Keyframe recovery |
| الجودة بتقع فجأة | Congestion في الـbandwidth | Adaptive bitrate |

وأهم سؤال: **لو الـnetwork بقت أسوأ، نعمل إيه؟**

في robot شغال real-time، **المعلومة الجديدة أهم من القديمة**. إنك تعرض frame من ثانيتين ممكن يبقى أسوأ من إنك تـdrop الـframe ده وتعرض اللي بعده. بس خلّي بالكم: لو رميت compressed packets بشكل عشوائي، الـframes اللي بعدها ممكن تبوظ لحد الـkeyframe الجاي، لأنها معتمدة عليها كـreference.

## 7. Streaming and Computer Vision ⏱️ 11:40

🎞️ **Slide 43** — The robot's eyes only see what the encoder kept

حاجة الفريق عمره ما ظبطها: الـ**object detection** والـ**3D reconstruction** والـ**autonomous movement** والـ**SLAM**. لو بيشتغلوا على الـstream فوق، فهم بيورثوا كل قرار في الـencoding:

- الـblocking والـblur بيمسحوا الـcorners اللي الـSLAM بيـtrack عليها.
- دراسة على YOLOv5 لقت إن الـdetection مستحمل الـcompression المتوسط، بس بيقع مع الـcompression القوي، **خصوصاً في الإضاءة الضعيفة والحركة السريعة**. وده بالظبط وصف الفيديو تحت الميه.
- الـframe القديم بيخلي الـautonomous controller يعمل overshoot.

والقواعد: نشغّل الـCV جنب الـraw frames على الـROV لو نقدر. ولو فوق، يبقى ليه **stream مخصوص** بـbitrate أعلى ومن غير B-frames. والـphotogrammetry تتعمل من **stills متسجلة** مش من الـlive stream.

## 8. The Engineering Mindset ⏱️ 12:20

🎞️ **Slide 78** — Take it back to the ROV

هسيبكم بتلات أسئلة لازم كل الفريق يعرف إجابتها:

1. عندنا **bandwidth** قد إيه **فعلاً**؟ متقاس، مش مكتوب على الكرتونة.
2. الـpilot يستحمل **latency** قد إيه؟
3. إيه اللي حيحصل لما الـ**network أو الـhardware يقع**؟

ورسالة واحدة:

> **Don't optimize for the best-looking video. Optimize for the best information the operator can receive in real time.**
>
> متدوّرش على أحلى فيديو. دوّر على أحسن معلومة توصل للـpilot في الوقت الحقيقي.

كل الـdemos والـcode والـnotebook موجودين في الـrepo بتاعنا على GitHub. جرّبوا، وغيّروا setting واحد، و**توقعوا قبل ما تشغّلوا**.

شكراً ليكم!
