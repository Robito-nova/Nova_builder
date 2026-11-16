# NOVA Builder — Genel Bakış

NOVA Builder, tek bir programlama dili veya tek bir UI teknoloji bağımlılığına sıkışmayan, evrensel şekilde paketlenebilen uygulama geliştirme platformudur. Builder, geliştirme ortamı; Build System, derleme ve paketleme altyapısı; Runtime, uygulamanın çalıştırılmasını sağlayan birim; Package Format ise dağıtım arşividir.

## Temel hedefler

- hafiflik
- yüksek hız
- düşük kaynak tüketimi
- çoklu dil desteği
- modüler yapı
- genişletilebilir derleme sistemi
- standart `.nova` paketi
- düşük donanımlı cihaz uyumu

## Temel ayrım

### 1. NOVA Builder
Geliştiricinin kod yazdığı, projeleri yönettiği, arayüzü kullandığı ortamdır.

### 2. NOVA Build System
Proje algılaması, dil tespiti, araç zinciri seçimi, bağımlılık çözümü, derleme, çıktı üretimi ve `.nova` paketleme işlemlerini yönetir.

### 3. NOVA Runtime
İçerilen uygulamanın çalıştırılmasını sağlar. Build System tarafından üretilen paketi, runtime tarafından açar ve gerekli çalışma ortamını sağlar.

### 4. NOVA Package Format
`.nova` uzantılı, standart manifest içeren, imza ve doğrulama bilgileri taşıyan dağıtım paketidir.

## İlk aşama notu

Bu aşamada yalnızca temel mimari, manifest ve paket formatı çalışır. Görsel arayüz, dil adaptörleri ve paket doğrulayıcı güvenlik katmanları, sonraki aşamalara taşınabilir; ancak tasarımın temel iskeleti burada tanımlanmıştır.
