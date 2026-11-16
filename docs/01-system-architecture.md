# Sistem Mimarisi

## Yüksek seviyeli mimari

NOVA Builder, 6 ana katmandan oluşur:

1. UI Layer
   - proje gezgini
   - editör
   - terminal
   - çıktı paneli
   - yapılandırma ekranı

2. Application Layer
   - proje yöneticisi
   - şablon yöneticisi
   - kaynak yöneticisi
   - proje yapılandırma yöneticisi

3. Language Integration Layer
   - dil tanımlayıcılar
   - dil adaptörleri
   - çalışma ortamı bağlayıcıları

4. Build Layer
   - proje algılama
   - araç zinciri bulma
   - bağımlılık çözme
   - derleme ve paketleme

5. Security and Validation Layer
   - manifest doğrulama
   - bağımlılık kontrolü
   - imza ve paket bütünlüğü
   - izin politikaları

6. Runtime & Packaging Layer
   - `.nova` paketi oluşturma
   - runtime yükleme
   - çalışma ortamı yönetimi

## Etkileşim modeli

- UI, Application Layer üzerinden sistem işleyişini yönetir.
- Application Layer, Build System ve dil adaptörlerine istek gönderir.
- Build System, uygun araç zinciri ve çalışma ortamı ile derlemeyi yürütür.
- Runtime, oluşturulan paketi çalıştırmak için gerekli ortamı hazırlar.
- Security Layer, her paket ve derleme adımında kontrol sağlanır.

## Katman ayrımı prensibi

NOVA Builder'ın bir bileşeninin başka bir bileşene yüklü şekilde birleştirilmesi yerini, açık arayüzler ve ayrılmış iş akışı kullanılmalıdır.

Örnek:

- Proje Yöneticisi, kaynak kod editörü ve paket yöneticisini doğrudan bilmez.
- Kod Editörü, derleme detayını bilmez.
- Build System, UI katmanından bağımsız çalışır.
- Runtime, Builder ile aynı proses içinde çalışmak zorunda değildir.

## Düşük kaynak tasarımı

- asenkron iş parçacığı kullanımı
- arka planda derleme
- UI'ı ağırlaştırmayan tek pencere mantığı
- gereksiz animasyonlardan kaçınma
- 2 çekirdek/1.8 GHz hedefinde çalışma

## Genişletilebilirlik yaklaşımı

Yeni bir dil eklemek için:

1. yeni bir dil adaptörü tanımlanır
2. build recipe ve runtime mapping eklenir
3. manifest türü ve izin politikaları tanımlanır
4. paket doğrulayıcı buna göre genişletilir

Böylece derleme sistemi yeniden yazılmaz; adaptör eklenir.
