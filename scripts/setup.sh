#!/bin/bash

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

clear
echo -e "${BLUE}🚀 Iniciando setup do ambiente...${NC}\n"

if [ ! -f .env ]; then
    echo -e "${YELLOW}⚙️ Gerando arquivo .env...${NC}"
    cat <<EOF > .env
DB_NAME=tetrisdb
DB_USER=admin
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=27017
EOF
    echo -e "${GREEN}✅ .env criado.${NC}"
else
    echo -e "${YELLOW}⚠️ .env já existe. Pulando...${NC}"
fi

if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}📦 Criando ambiente virtual (.venv)...${NC}"
    python3 -m venv .venv
    echo -e "${GREEN}✅ Ambiente virtual criado.${NC}"
else
    echo -e "${YELLOW}⚠️ .venv já existe.${NC}"
fi

echo -e "${YELLOW}📥 Instalando dependências do Python...${NC}"
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo -e "${GREEN}✅ Dependências instaladas.${NC}"

echo -e "${YELLOW}🐳 Subindo infraestrutura Docker...${NC}"
docker-compose up -d --build

echo -e "\n${GREEN}=========================================${NC}"
echo -e "${GREEN}🚀 SETUP CONCLUÍDO COM SUCESSO!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo -e "\nPara jogar, use:"
echo -e "${BLUE}make run${NC}"
