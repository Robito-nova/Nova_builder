# Bileşenler ve Sorumluluklar

## 1. Proje Yöneticisi
Sorumluluklar:
- yeni proje oluşturma
- proje açma ve kapatma
- proje yapısı yönetimi
- proje bağımlılıklarının izlenmesi
- proje konfigurasyonunun yüklenmesi ve kaydedilmesi

Arayüzler:
- `create_project()`
- `open_project()`
- `save_project()`
- `list_projects()`

## 2. Kod Editörü
Sorumluluklar:
- kaynak kod düzenleme
- çoklu dil destekli syntax vurgulama
- temel arama ve değiştirme
- editör seçenekleri

Arayüzler:
- `open_file()`
- `save_file()`
- `get_document_state()`
- `format_code()`

## 3. Dil Entegrasyon Yöneticisi
Sorumluluklar:
- dil tanımı ve eşleme
- derleyici/yorumlayıcı bağlama
- çalışma ortamı ve standard library görünürlüğü
- dil adaptörü kaydı

Arayüzler:
- `register_adapter()`
- `detect_language()`
- `resolve_runtime()`

## 4. Derleme Sistemi
Sorumluluklar:
- yapılandırma algılama
- hedef platform belirleme
- araç zinciri seçimi
- çıktı üretimi
- hataları ve uyarıları raporlama

Arayüzler:
- `build(project, target)`
- `clean(project)`
- `inspect(project)`

## 5. Derleyici ve Araç Zinciri Yöneticisi
Sorumluluklar:
- derleyici kurulum ve doğrulama
- sürüm eşleşmesi
- toolchain cache yönetimi
- ortam değişkenleri ve aracı yolu kontrolü

Arayüzler:
- `resolve_toolchain()`
- `install_toolchain()`
- `validate_toolchain()`

## 6. Bağımlılık Yöneticisi
Sorumluluklar:
- kütüphane çözümü
- lockfile ve versiyon takibi
- bağımlılık doğrulama
- güvenlik taraması ve uyumluluk kontrolü

Arayüzler:
- `resolve_dependencies()`
- `install_dependencies()`
- `verify_dependency_integrity()`

## 7. Paket Yöneticisi
Sorumluluklar:
- `.nova` paket oluşturma
- yayımlama ve sürüm yönetimi
- paket listesi ve metadata yönetimi

Arayüzler:
- `create_package()`
- `publish_package()`
- `list_packages()`

## 8. Paket Doğrulayıcı
Sorumluluklar:
- manifest doğrulama
- arşiv yapısı kontrolü
- sağlamlık ve bütünlük doğrulama
- izin politikalarının uygulanması

Arayüzler:
- `validate_manifest()`
- `validate_package_structure()`
- `verify_checksum()`

## 9. Uygulama Önizleme Sistemi
Sorumluluklar:
- uygulama çalıştırma önizleme
- ortam simülasyonu
- log yakalama
- kullanıcı davranış testi

## 10. Hata Ayıklama Sistemi
Sorumluluklar:
- hata yakalama ve kod konumlandırma
- breakpoints yönetimi
- adım adım izleme
- çalışma zamanında değişken ve stack izleme

## 11. Kaynak Yöneticisi
Sorumluluklar:
- asset ve resource yönetimi
- görsel, ses, simge, font yükleme
- dosya izleme ve tema yönetimi

## 12. Şablon Yöneticisi
Sorumluluklar:
- hazır proje şablonlarını sunma
- dil ve platform şablonları
- örnek uygulama oluşturma

## 13. Proje Yapılandırma Yöneticisi
Sorumluluklar:
- proje ayarları
- hedef platform yapılandırması
- build profile ve runtime ayarları
- manifest bağlamı yönetimi

## Arayüz tasarımı prensibi

Her modül, diğer modüllerdeki detayları bilmek zorunda değildir. Arayüzler işlevsel ve soyut tutulmalıdır. Bu sayede dil adaptörlerinin, farklı target mimarilerinin veya yeni manifest sürümlerinin eklenmesi kolaylaşır.
