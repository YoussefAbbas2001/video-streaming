# Video 2 — The ROV Streaming Pipeline and Its Bottlenecks
## الفريم بيمشي إزاي من الكاميرا لعين الـpilot، وبيتأخر فين

| | |
|---|---|
| **المدة** | ≈ 7 دقايق (حوالي 900 كلمة كلام) |
| **الـSlides** | 13 · 11 · 12 · 39 · 33 · 34 · 36 · 37 · 44 |
| **الـDemos** | Demo 2: Find the bottleneck (`sender.sh` + `receiver.sh` + `monitor.py` + `impair.sh`) · الـreceiver buffering |
| **قبل التسجيل** | اقرا `demos/02_pipeline/bottleneck_lab.md` · افتح 3 terminals · جرّب `sudo ./impair.sh lo clear` إنه شغال · لو فيه SBC جنبك، شغّل `camera_inventory.sh` عليه |

> 🎞️ = slide · 🧪 = Demo · 🎥 = شاشة/B-roll · ⏱️ = الوقت

---

## Opening ⏱️ 0:00

أهلاً بيكم تاني، أنا يوسف عباس، وده الفيديو التاني في سلسلة الـStreaming.

في الفيديو اللي فات قلنا إن الـvideo هو عين الـpilot، وإن الـcompression هو اللي مخلي ده ممكن أصلاً. النهارده حنمشي ورا **frame واحد** من لحظة ما الضوء يخبط في الـsensor لحد ما يظهر على شاشة الـpilot، ونشوف كل محطة ممكن تبقى **bottleneck**.

## Content Overview

1. الـPipeline كامل: من الـsensor لحد الـdisplay
2. أول محطة: الكاميرا، USB ولا IP؟
3. التلات أنواع الأساسية للـbottlenecks
4. الـProcessing: الـJetson Nano والـRaspberry Pi 5، وهل الـPi 5 ينفع يبقى replacement؟
5. الـReliability: اللي حصل في 2023 بسبب الحرارة
6. الـDemo: نلاقي الـbottleneck بإيدينا
7. إزاي نقيس كل ده

يلّا بينا!

---

## 1. The Complete Pipeline ⏱️ 0:40

🎞️ **Slide 13** — Following a frame

الـframe بيعدي على المحطات دي بالترتيب:

**Camera ← Capture ← Preprocessing ← Encoder ← Packetization ← Network/Tether ← Jitter buffer ← Decoder ← Rendering ← Display**

كل محطة بتاخد شوية وقت، وكل محطة ممكن تبقى هي اللي خانقة الـsystem كله. وأهم فكرة في الفيديو ده:

> الـ**Latency بتتجمع**: L_total = L_capture + L_encode + L_network + L_buffer + L_decode + L_render

مثال توضيحي، مش أرقام الـROV بتاعنا: capture 10 ms، encoding 15، network 20، buffering 15، decoding 5، rendering 8، يعني حوالي **76 ms**. ولو أي محطة فيهم عملت buffer زيادة، الرقم ده يبقى ثواني.

🎞️ **Slide 11** — Where does encoding happen?

والسؤال اللي لازم كل الفريق يعرف إجابته: **الـencoding بيحصل فين عندنا؟** جوه الكاميرا؟ على الـSBC؟ ولا على الـlaptop فوق؟ (والأخير ده ما بيوفرش أي bandwidth في الـtether أصلاً.)

## 2. First Station: USB vs IP Cameras ⏱️ 1:30

🎞️ **Slide 12** — USB cameras vs IP cameras

إحنا فعلاً بنعمل stream لـ8 كاميرات، وفيه أنظمة الـNVR بتاعة المراقبة بتستقبل عشرات الكاميرات. الاتنين شغالين، بس كل واحد حاطط الـbottleneck في مكان مختلف:

- الـ**USB camera**: الـbus بتاع USB 2.0 فيه 480 Mb/s **مشتركين** بين كل الأجهزة اللي عليه، والكابل الـpassive أقصاه 5 متر. لو الكاميرا بتطلع raw أو MJPEG يبقى الـSBC هو اللي بيعمل encode. لكن فيه كاميرات زي الـBlue Robotics low-light بتعمل **H.264 جوه الكاميرا نفسها**.
- الـ**IP camera**: الكاميرا بتعمل encode بنفسها دايماً، وليها port Ethernet لوحدها، والكابل لحد 100 متر، وبتاخد power بالـPoE. وده سر إن الـNVR بيستحمل عشرات الكاميرات: هو ما بيعملش encode خالص، بيستقبل بس.

الفكرة: **مين اللي بيعمل encode؟** ده السؤال اللي بيحدد كل حاجة بعد كده.

## 3. Three Bottleneck Categories ⏱️ 2:20

🎞️ **Slide 42** — Where the milliseconds go (ESTIMATE)

عندنا تلات أنواع:

**أ. Processing bottleneck**: الـCPU أو الـGPU مضغوط، أو الـcolor conversion واخدة وقت، أو الـencoder مش ملاحق على الـframes اللي داخلة.

**ب. Network bottleneck**: الـbandwidth مش كفاية، أو فيه packet loss، أو jitter، أو congestion و retransmissions.

**ج. Buffering & synchronization bottleneck**: frames مستنية في queues، أو الـdecoder متأخر، أو الـbuffering زيادة عن اللزوم، أو بنعرض frame قديم بدل أحدث واحد.

ومن تجربتي، النوع التالت ده أكتر واحد بيتنسي، وغالباً هو اللي بيعمل أكبر delay.

## 4. Processing: Jetson Nano vs Raspberry Pi 5 ⏱️ 3:00

🎞️ **Slide 36** — Who does the work? Software vs hardware encoding

الـ**software encoding** مرن وجودته عالية، بس بياكل CPU وبيسخن. الـ**hardware encoder** قطعة silicon مخصوصة، شبه ما بتاخدش CPU، بس الـcapacity بتاعتها ثابتة.

🎞️ **Slide 37** — Jetson Nano vs Raspberry Pi 5

السنة دي الفريق عايز ينقل من الـJetson Nano للـRaspberry Pi 5، والـPi 5 لسه ما اتجربش عندنا. فخلونا نبص على الحقايق:

- الـJetson Nano فيه **hardware encoder**: يعمل 4 streams 1080p30 أو 9 streams 720p30.
- الـPi 5 **ما فيهوش hardware H.264 encoder خالص**. الـCPU بتاعه أسرع بكتير، بس الـencoding كله software. وتجربة Raspberry Pi نفسها في 2026 قالت إن stream واحد 1080p30 بالـlow-latency settings بياخد حوالي **62 لـ90% من core كامل**.

🎞️ **Slide 39** — Can the Raspberry Pi 5 replace the Jetson Nano?

فالإجابة: **على حسب مين بيعمل encode.**

- لو الكاميرات بتعمل H.264 بنفسها، يبقى الـPi 5 بديل ممتاز، لأنه بيمرّر الـpackets وبس.
- لو الـSBC لازم يعمل encode لكذا كاميرا raw، يبقى الـNano أحسن بكتير.
- لو عايزين computer vision على الـROV، الـNano عنده GPU، والـPi 5 محتاج الـAI HAT+.

ومهم كمان: الـJetson Nano developer kit بقى end of life. فالقرار لازم يتاخد بالقياس مش بالإحساس: **soak test** بـ8 streams لمدة 30 دقيقة جوه الـenclosure المقفول.

## 5. Reliability: The 2023 Heat Failure ⏱️ 4:10

🎞️ **Slide 40** — When the stream died from heat

في 2023، في trial في المسابقة، الـstreaming وقف خالص بسبب الحرارة على الـSBC. والسلسلة كانت كده:

**hull مقفول ← مفيش هوا ← encoding شغال طول الوقت ← الـCPU يوصل 80 درجة ← الـfirmware يعمل throttling ← الـencoder يبطّأ ← الـframes تتراكم وتقع ← الـstream يقف قدام الحكام.**

وأول حاجة لازم نفهمها: المروحة جوه hull مقفول بتقلّب الهوا السخن وبس. الحرارة لازم **تطلع من الـhull للميه**. والحل خمس خطوات:

1. **Measure**: نسجل الحرارة والـthrottling كل ثانية
2. **Design**: heat path من الـSBC لجسم الـROV للميه
3. **Reduce**: نخلي الكاميرات تعمل encode
4. **Soak-test**: نجرب 30 دقيقة في ميه دافية قبل أي مسابقة
5. **Show**: نعرض الحرارة للـpilot، ونطلع warning عند 75 درجة

## 6. Demo 2 — Find the Bottleneck ⏱️ 5:00

🧪 **Demo (حوالي 90 ثانية)**: تلات شاشات:

```bash
./demos/02_pipeline/sender.sh                      # terminal 1: الـROV
python3 demos/02_pipeline/monitor.py --iface lo    # terminal 2: الـmonitor
./demos/02_pipeline/receiver.sh                    # الشاشة: الـpilot
```

وبعدين نغيّر حاجة واحدة بس كل مرة، **وقبل ما ننفذ، اسأل: مين حيبقى الـbottleneck؟**

1. `RES=1920x1080` → الـCPU يطلع → **processing**
2. `sudo ./impair.sh lo limit 1mbit` → الـlatency تزيد كل ثانية والصورة تبوظ → **network**
3. `sudo ./impair.sh lo delay 150ms` → الصورة سلسة بس متأخرة → **network delay**
4. `./receiver.sh --plain` جنب `./receiver.sh`، وبص على `vq=` → ffplay العادي مخزّن حوالي 1.2 MB فيديو، والـlow-latency flags حوالي 23 KB بس → **buffering**

🎥 خلي الـmonitor ظاهر في الكادر: الـCPU، والـMb/s قصاد الـbudget 70%، والحرارة.

وفي الآخر لازم: `sudo ./impair.sh lo clear`.

## 7. How to Measure All of This ⏱️ 6:20

🎞️ **Slide 47** — Your measurement toolbox

كل رقم قلناه النهارده ليه tool بيقيسه: `iperf3` للـthroughput، و`ethtool` للـlink speed، و`iftop` و`nload` للـbandwidth المستخدم، و`tegrastats` و`vcgencmd` للـCPU والحرارة، و`chrome://webrtc-internals` للـbrowser، والـglass-to-glass للـlatency الحقيقية.

كل ده مكتوب بالتفصيل، بالـcommands، في `docs/measuring-performance.md` في الـrepo.

## Takeaway ⏱️ 6:40

> الـbottleneck نادراً ما بيكون في الكابل. غالباً بيبقى في **الـencoder** أو **الـbuffer** أو **الحرارة**، ومش حتعرفه غير لما **تقيس**.

في الفيديو الجاي، وده أهم واحد، حنفتح الـencoder نفسه من جوه: بيضغط الفيديو إزاي، وكل setting بيأثر على الـpilot إزاي.

شكراً ليكم!
