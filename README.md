# Folder Sync 

## Opis projektu
Ten projekt to aplikacja GUI zbudowana przy użyciu PyQt6, służąca do synchronizacji folderu edytowanego na różnych urządzeniach używając systemu Git. Program został stworzony z myślą o osobach niezapoznanych z Git'em, umożliwia podstawowe operacje na repozytorium oraz konfiguracje klucza SSH, aby uzyskać dostęp do prywatnego repozytorium. 

Aplikacja jest dostosowana do kompilacji z użyciem bibliotek takich jak pyinstaller. Skompilowany plik jest umieszczony w folderze exe. Wszystkie pliki znajdujące się w tym folderze są niezbędne do jej poprawnego działania. Aplikacja została skompilowana za pomocą komendy:
```cmd
pyinstaller main.py -D -w --noconfirm --add-data ../assets/loading.gif:. --add-data ../LICENSE:. --specpath build --contents-directory assets --distpath .
```

## Propozycja Zastosowania 
Aplikacja może służyć jako element usprawniający działanie modów do gry umożliwiających udostępnianie gry innym graczom (i granie jednocześnie jak to oferuje Essential Mod do Minecraft'a). Problem pojawia się, gdy osoba będąca właścicielem pliku nie jest dostępna, nikt poza nią nie może włączyć 'serwera'. Aplikacja ta umożliwia synchronizowanie zapisu gry między urządzeniami. 
## Wymagania
Do uruchomienia aplikacji potrzebujesz:
1. W wersji nieskompilowanej: 
- Python 3.8+
- Biblioteka PyQt6
- Biblioteka gitpython 
- Biblioteka paramiko
- Oprogramowanie git z agentem ssh
2. W wersji skompilowanej:
- Oprogramowanie git z agentem ssh

## Konfiguracja aplikacji
### Wersja nieskompilowana:
1. Sklonuj bądź pobierz repozytorium
2. Skonfiguruj wymagane biblioteki
```cmd
pip install PyQt6 gitpython paramiko
```
3. Uruchom aplikacje 
```cmd
python main.py
```
### Wersja skompilowana
Nie wymaga konfiguracji, wystarczy pobrać aplikacje (cały folder skompresowany exe.zip) rozpakować ją i włączyć plik wykonywalny main.exe.

## Inne konfiguracje
Aby aplikacja działała, potrzebna jest konfiguracja repozytorium git (np. na githubie). Aplikacja przy pierwszym włączeniu zapyta o ścieżkę folderu w chmurze. Należy wkleić tam ścieżkę HTTPS lub SSH. Dla prywatnego repozytorium konieczne jest użycie ścieżki ssh oraz skonfigurowanie klucza SSH. Do zdalnego repozytorium dodaje się klucz publiczny (w ustawieniach kategoria Deploy Keys), klucz musi mieć uprawnienia READ/WRITE. Aplikacja umożliwia stworzenie tego klucza. Konieczne jest dodanie klucza publicznego do repozytorium zaraz po otrzymaniu klucza publicznego. 

## Struktura projektu
- main.py: inicjalizacja programu 
- Program.py: Główna część aplikacji, zarządza logiką programu, interakcjami z Git, SSH oraz komunikacją z GUI.
- MainWindow.py: obsługa GUI 
- globals.py: Zawiera zmienne globalne i funkcje pomocnicze, takie jak obsługa mutexów, ścieżki do plików i mechanizmy zarządzania błędami.

## Główne funkcje

### Obsługa Git: 
- Klonowanie repozytorium git do wybranej lokalizacji (możliwe jest klonowanie do niepustego folderu, pliki zostaną przywrócone do niego po zakończeniu klonowania)
- Wczytywanie danych ze zdalnego repozytorium
- Wysyłanie zmian do repozytorium
- Rozwiązywanie prostych konfliktów 
### Obsługa SSH
- Aplikacja konfiguruje klucz ssh dla aplikacji. Na chwilę obecną nie obsługuje wielu kluczy. Jedyny obsługiwany typ klucza ssh to RSA.
- Użytkownik może wczytać nowy klucz do aplikacji lub wygenerować go z jej pomocą
### Aplikacja używa biblioteki PyQt6 do tworzenia okienkowego interface'u użytkownika 
