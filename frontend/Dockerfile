FROM node:18-alpine
WORKDIR /app
COPY package.json ./
# package-lock.json이 있으면 복사, 없으면 무시되도록 (와일드카드 사용불가하지만 있으면 좋음)
# COPY package*.json ./ 
RUN rm -rf node_modules package-lock.json && npm install
COPY . .
EXPOSE 3000
CMD ["npm", "start"]
