<p align="center">
  <img src="https://api.iconify.design/lucide/layout-grid.svg?color=%23bd93f9" alt="Grid Icon" width="50" />
</p>

<h1 align="center"><strong>Python Tetris</strong></h1>

<p align="center">
  <img src="https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54" height="25" />
  <img src="https://img.shields.io/badge/mongodb-47A248?style=for-the-badge&logo=mongodb&logoColor=white" height="25" />
  <img src="https://img.shields.io/badge/docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" height="25" />
  <img src="https://img.shields.io/badge/license-MIT-bd93f9?style=for-the-badge" height="25" />
</p>

<p align="center">
  <a href="#sobre">Sobre</a> • 
  <a href="#arquitetura">Arquitetura</a> •
  <a href="#releases">Releases</a> •
  <a href="#instalacao">Instalação</a> •
  <a href="#docker">Docker & Seed</a> •
  <a href="#licenca">Licença e Disclaimer</a>
</p>

<p align="center">
  <b>Uma implementação clássica do jogo Tetris focada em Programação Orientada a Objetos (POO) e persistência de dados com MongoDB.</b>
</p>

---

<h2 id="sobre">📌 Sobre</h2>

Este projeto é um clone do **Tetris** desenvolvido para fins educacionais. O objetivo principal foi aplicar conceitos avançados de **POO** em Python e integrar o jogo com um banco de dados **NoSQL** para gerenciar um sistema de _Leaderboard_ global.

### Funcionalidades

- 🧩 Lógica de rotação e colisão precisa.
- 🏆 Sistema de Ranking (Top 5) persistente.
- 🐳 Infraestrutura de banco de dados totalmente conteinerizada.
- 📈 Curva de dificuldade progressiva baseada em níveis.

---

<h2 id="arquitetura">🏗️ Arquitetura (POO)</h2>

O projeto segue princípios de **Programação Orientada a Objetos** para garantir um código modular, desacoplado e de fácil manutenção. A estrutura é dividida em quatro camadas lógicas fundamentais:

- **Motor do Jogo (Core Logic):** Camada responsável pelas regras de negócio, incluindo a manipulação das peças (tetrominos), mecânicas de rotação, detecção de colisões e gerenciamento do grid.
- **Interface e Renderização:** Camada dedicada à saída visual e processamento de entrada de usuário via Pygame. Gerencia o ciclo de atualização da tela, carregamento de texturas e efeitos sonoros localizados na pasta `assets/`.
- **Persistência de Dados:** Interface de comunicação com o MongoDB. Centraliza a lógica de salvamento e recuperação de recordes (leaderboard), isolando as consultas ao banco do restante do código.
- **Orquestração (Controller):** O ponto de entrada da aplicação que conecta o motor lógico à interface visual e ao banco de dados, controlando o fluxo dos estados do jogo (Menu, Partida, Game Over).

---

<h2 id="releases">🏁 Rodar sem compilar</h2>

Se você não deseja configurar o ambiente Python manualmente, pode utilizar os executáveis pré-gerados na seção de **Releases**.

👉 **[Baixar o último release](https://github.com/alexbeldam/tetris/releases/latest)**

### Como executar:

---

<h2 id="instalacao">🛠️ Instalação e Uso</h2>

### Pré-requisitos

- **Python 3.11+**
- **Docker & Docker Compose** (para o banco de dados)

### Passos para rodar

1. **Clone o repositório:**

   ```bash
   git clone [https://github.com/alexbeldam/tetris.git](https://github.com/alexbeldam/tetris.git)
   cd tetris
   ```

2. **Configure o ambiente:**

   ```bash
   chmod +x scripts/setup.sh
   .scripts/setup.sh
   ```

3. **Inicie o jogo:**

   ```bash
   python src/main.py
   ```

---

<h2 id="docker">🐳 Docker & Leaderboard Seed</h2>

O projeto utiliza um container MongoDB configurado para auto-inicialização. O banco é automaticamente populado com um placar inicial para simular a dificuldade.

- **Seeder Automático**: Localizado em `scripts/seeder.sh`, ele garante que os dados em `data/seed.js` sejam inseridos no banco assim que o container for criado.

---

<h2 id="licenca">⚖️ Licença e Disclaimer</h2>

### MIT License

Este software está licenciado sob a **MIT License**. Você é livre para usar, copiar e modificar o código fonte deste projeto. Veja o arquivo `LICENSE` para detalhes.

### Disclaimer

Este projeto é uma **implementação não oficial** para fins estritamente educacionais e de portfólio.

- **Tetris®** é uma marca registrada da _Tetris Holding, LLC_.
- Este projeto não é afiliado, endossado ou patrocinado pela _The Tetris Company_.
- Não utilize os assets originais (músicas ou imagens protegidas) para fins comerciais.

---

<h2 id="colaboradores">🤝 Colaboradores</h2>

<p align="center">
Um grande obrigado a todas as pessoas que contribuíram para este projeto.
</p>

<table align="center">
  <tr>
    <td align="center">
      <a href="https://github.com/alexbeldam">
        <img src="https://github.com/alexbeldam.png" width="100px" height="100px" alt="Foto do Alex"/><br>
        <sub><b>Alex</b></sub>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/bernardo-sabino">
        <img src="https://github.com/bernardo-sabino.png" width="100px" height="100px" alt="Foto do Bernardo"/><br>
        <sub><b>Bernardo</b></sub>
      </a>
    </td>
  </tr>
</table>

---

<p align="center">
Feito com 👾 para o trabalho prático de POO da UFMG
</p>
