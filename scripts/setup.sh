#!/bin/bash

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'
ENV_NAME=$(bash scripts/get-meta.sh env_name)

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

echo -e "${YELLOW}📦 Sincronizando ambiente Conda (${ENV_NAME})...${NC}"
make --no-print-directory env-sync

echo -e "${YELLOW}🐳 Buildando imagens Docker locais...${NC}"
make --no-print-directory docker-build

echo -e "${YELLOW}🐳 Subindo infraestrutura Docker...${NC}"
make --no-print-directory start

echo -e "\n${GREEN}=========================================${NC}"
echo -e "${GREEN}🚀 SETUP CONCLUÍDO COM SUCESSO!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo -e "\nPara jogar, use:"
echo -e "${BLUE}make run${NC}"
