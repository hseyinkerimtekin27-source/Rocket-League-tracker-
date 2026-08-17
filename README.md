# RL Stats Tracker — Kurulum Rehberi

Rocket League oynarken arka planda çalışan, her maçtan sonra istatistiklerini
**otomatik** kaydeden tepsi (tray) uygulaması. Maç başına elle veri girmene
gerek yok.

## Neyi otomatik yapıyor, neyi yapmıyor

**Otomatik (elle girmene gerek yok):**
- Galibiyet / mağlubiyet
- Gol, asist, kurtarış, şut sayısı
- MVP olup olmadığın (skor bazlı tahmin — Rocket League'in kendi ödül
  animasyonuyla neredeyse her zaman örtüşür)
- Harita ve playlist (Doubles, Standard vb.)
- Tarih/saat

**Elle (ama maç başına değil, sadece rank atladığında bir kez):**
- Rank. Rocket League'in kaydettiği replay dosyaları rankını içermiyor
  (Psyonix bu bilgiyi oraya yazmıyor), bu yüzden tam otomatik çekilemiyor.
  Tepsi menüsünden "Rankımı Güncelle" ile 5 saniyede güncelleyebilirsin.
  İstersen ileride BakkesMod entegrasyonuyla bunu da otomatikleştirebiliriz.

## Kurulum — Yöntem A: Python kurmadan, GitHub Actions ile (önerilen)

Bilgisayarına Python kurmana gerek yok. .exe, GitHub'ın ücretsiz sağladığı
gerçek bir Windows makinesinde otomatik derlenir, sen sadece indirirsin.

1. [github.com](https://github.com) üzerinde ücretsiz bir hesap aç (yoksa).
2. Sağ üstten **"New repository"** ile yeni, **public** bir repo oluştur
   (ör. adı `rl-stats-tracker`). "Add README" kutucuğunu İŞARETLEME.
3. Bu zip'in içindeki dosyaları o reponun sayfasında **"uploading an existing file"**
   linkinden sürükle-bırak ile yükle (klasör yapısını koruyarak — `.github` klasörü dahil).
   Terminal kullanmak istersen alternatif:
   ```
   git init
   git add .
   git commit -m "ilk yükleme"
   git branch -M main
   git remote add origin https://github.com/KULLANICI_ADIN/rl-stats-tracker.git
   git push -u origin main
   ```
4. Repo sayfanda üstteki **"Actions"** sekmesine git. "Windows exe derle"
   workflow'u otomatik başlamış olacak (birkaç dakika sürer, yeşil tik
   bekleniyor).
5. Tamamlanınca workflow'a tıkla, en altta **"Artifacts"** bölümünden
   **RLStatsTracker-windows** dosyasını indir — içinde `RLStatsTracker.exe` var.
6. `.exe` dosyasını çalıştır, bittiğinde bir Windows uyarısı çıkarsa
   ("Windows korudu bilgisayarınızı") **"Daha fazla bilgi" → "Yine de çalıştır"**
   de — bu, imzasız/az bilinen uygulamalarda normaldir, GitHub Actions'ın
   kendi ürettiği temiz bir dosyadır.

## Kurulum — Yöntem B: Kendi bilgisayarında Python ile

1. **Python 3.10+ kur:** https://python.org (kurulumda "Add to PATH" kutucuğunu işaretle)
2. Bu klasördeki dosyaları bir yere çıkar (ör. `Belgeler\RLStatsTracker`)
3. **`build_exe.bat`** dosyasına çift tıkla. Otomatik olarak:
   - Gerekli paketleri kurar
   - `RLStatsTracker.exe` dosyasını `dist` klasörüne üretir
4. `dist\RLStatsTracker.exe` dosyasını çalıştır.
   - İlk açılışta senden Rocket League'deki görünen adını soracak (Epic/Steam adın) — sadece bir kere.
   - Sonra sistem tepsisine (saatin yanındaki simgeler) yerleşir.

## Render hakkında not

Bu uygulama senin bilgisayarındaki Rocket League replay dosyalarını okuyarak
çalışır, bu yüzden **Render gibi bir bulut sunucuya deploy edilemez** — bulut
sunucunun senin oyun dosyalarına erişimi olamaz. Eğer ayrıca tarayıcıdan
açılan, Render'da barındırılabilecek bir web panosu istersen (elle veri
girdiğin ama her cihazdan erişebileceğin), bunu ayrı bir proje olarak
hazırlayabilirim — söylemen yeterli.

## Windows açılışında otomatik başlatma

`dist\RLStatsTracker.exe` dosyasının kısayolunu şu klasöre koy:

```
Win + R  →  shell:startup  →  Enter
```

Kısayolu bu klasöre kopyalarsan, bilgisayar her açıldığında uygulama arka
planda otomatik başlar.

## Kullanım

- Ranked/casual bir maç oyna, maç bitip lobiye dönünce birkaç saniye içinde
  sağ altta bir bildirim çıkar: "Maç kaydedildi — Galibiyet 🏆 · 3 gol · 1 asist..."
- Tepsi simgesine sol tıkla → özet istatistik penceresi açılır.
- Sağ tık → menüden rank güncelleme, JSON dışa aktarma, çıkış.

## Verilerin nerede tutuluyor

`%APPDATA%\RLStatsTracker\stats.db` (SQLite). Kimseyle paylaşılmıyor, hiçbir
sunucuya gönderilmiyor — tamamen kendi bilgisayarında kalıyor.

## AI destekli eşleştirme analizi için

Tepsi menüsünden "Verileri Dışa Aktar (JSON)" dediğinde masaüstüne
`rl_stats_export.json` iner. Bu dosyanın içeriğini bana yapıştırırsan
(ya da daha önce sana verdiğim web tabanlı istatistik panosuna eklersen),
eşleştirmenin adaletli olup olmadığı ve performans trendin hakkında
yapay zeka destekli bir yorum çıkarabilirim.

## Bilinen sınırlamalar

- Rocket League'in replay formatı zaman zaman küçük güncellemelerle
  değişebiliyor. Eğer bir gün "Replay okunamadı" hatası almaya başlarsan
  (konsol penceresini görmek için `--windowed` yerine `--console` ile
  yeniden derleyebilirsin), bana haber ver, parser'ı güncelleriz.
- Sadece **online** maçlar replay dosyası üretir (yerel/split-screen maçlar
  hariç tutulabilir, oyun ayarına bağlı).
- Bu kaynak kodu bu sohbette test edemedim (bende çalışan bir Windows/Rocket
  League ortamı yok) — ilk çalıştırmada bir sorun çıkarsa hatayı bana
  yapıştır, birlikte düzeltelim.
