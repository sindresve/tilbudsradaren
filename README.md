# Tilbudsradaren
En app som skanner ukentlige tilbudsaviser fra lokale dagligvarekjeder og varsler deg når produktene du kjøper ofte er på tilbud. Laget for å gjøre studenthverdagen litt billigere.

## Hvordan funker det?
- Skanner tilbudsaviser hver uke fra butikkene som du har skrudd på varslinger for
- Varsler deg når produkter du følger med på (ris, jylling, osv) dukker opp på tilbud
- Fin frontend hvor alt er samlet og oversiktlig

## Planlagt / kommer senere
- AI-chatbot som leser ukens tilbud, kjenner til dine preferanser og allergier, og foreslår middagsretter basert på det som faktisk er på tilbud
- Flere varslingskanaler og finpuss av eksisterende funksjoner
- Skrivebordsvarsel (når nettsiden er åpen eller programmet kjører lokalt)

## Tech stack
- Backend laget i Python (FastAPI)
- Data lagret i lokal SQLite Database
- AI-modeller:
    - Google Gemini for innhenting av tekst fra bilde/pdf filene (lokale modeller vil bruke ekstremt lang tid + det kan bli mye feil)
    - Lokal AI modell for AI-chatbot
- Frontend laget med NextJS, React, Typescript, Tailwindcss

## Varslinger
Varslinger kan blir sendt gjennom:
- E-post
- Discord webhook

## Kom i gang

### 1. Klon repoet
```bash
git clone https://github.com/sindresve/tilbudsradaren.git
cd tilbudsradaren
```
### 2. Backend setup
```bash
# Backend
cd backend
python -m venv venv # Du kan velge om du vil opprette et virtuelt miljø eller ikke (anbefalt)
venv\Scripts\activate.bat
pip install -r requirements.txt
python -m uvicorn api.main:app --reload --port 8000
```

### 3. Frontend setup
```bash
# Frontend
cd ../frontend
npm install
npm run dev
```

### 4. Oppsett av Programmet
Både backend og frontend må kjøre samtidig. Åpne deretter frontend i nettleseren — der blir du guidet gjennom noen spørsmål og instrukser for å sette opp det du trenger.

Når oppsettet er fullført finner du en Start-knapp i venstre menyen, sammen med:

- hvilken uke det er
- timer med hvor lang tid til neste scan
- en Stopp-knapp