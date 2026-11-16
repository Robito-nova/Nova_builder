# Performans Stratejisi

## Hedefler

- hızlı açılış
- düşük bellek tüketimi
- düşük CPU kullanımı
- yüksek erişilebilirlik
- düşük donanımlı cihaz uyumu

## Stratejiler

### 1. Yüksek verimli başlangıç
- uygulama başlatma sırasında gerekli olmayan modülleri ertele
- proje gezgini ve manifest bilgileri yalnızca ihtiyaç anında yükle

### 2. Asenkron yürütme
- derleme, paketleme ve dosya işlemleri arka planda çalıştırılır
- UI threadi kilitlenmez

### 3. Hafif arayüz
- animasyonları azalt
- ağır CSS ve görsel efektleri önle
- yerel dosya sistemine yüksek erişim gerektiren işlemleri sınırlı tut

### 4. Toolchain cache
- araç zincirleri önbelleklenebilir
- aynı derleyici ve runtime sürümleri tekrar kullanılabilir

### 5. Kaynak bazlı çıktı yönetimi
- build çıktıları ayrı bir çalışma alanında tutulur
- gereksiz dosya kopyalama minimum seviyeye düşürülür

## Ölçülebilir hedefler

- uygulama açılış süresi: çok düşük 1-3 saniye seviyesinde
- bellek kullanımı: hafif görevler için düşük/orta aralıkta kalır
- CPU: idling durumunda minimum seviyelerde tutulur

## Not

Bu hedefler, ASUS X550CA ve benzeri düşük güçlü sistemler için tasarlanan stratejilerdir. Daha güçlü sistemlerde daha fazla paralellik sağlanabilir ancak temel tasarım hafiflik üzerine kuruludur.
