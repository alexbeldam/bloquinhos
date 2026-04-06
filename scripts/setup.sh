#!/bin/bash

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'
ENV_NAME="block_env"

clear
echo -e "${BLUE}🚀 Iniciando setup do ambiente...${NC}\n"

if [ ! -f .env ]; then
    echo -e "${YELLOW}⚙️ Gerando arquivo .env...${NC}"
    cat <<EOF > .env
DB_NAME=blockdb
DB_USER=admin
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=27017
EOF
    echo -e "${GREEN}✅ .env criado.${NC}"
else
    echo -e "${YELLOW}⚠️ .env já existe. Pulando...${NC}"
fi

if ! conda info --envs | grep -q "$ENV_NAME"; then
    echo -e "${YELLOW}📦 Criando ambiente Conda ($ENV_NAME)...${NC}"
    conda env create -f environment.yml
    echo -e "${GREEN}✅ Ambiente criado.${NC}"
else
    echo -e "${YELLOW}⚠️ Ambiente '$ENV_NAME' já existe. Atualizando dependências...${NC}"
    conda env update -f environment.yml --prune
    echo -e "${GREEN}✅ Ambiente atualizado.${NC}"
fi

echo -e "${YELLOW}🐳 Subindo infraestrutura Docker...${NC}"
docker compose up -d --build

echo -e "\n${GREEN}=========================================${NC}"
echo -e "${GREEN}🚀 SETUP CONCLUÍDO COM SUCESSO!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo -e "\nPara jogar, use:"
echo -e "${BLUE}make run${NC}"
