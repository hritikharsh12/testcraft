FROM node:20-slim

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

EXPOSE 5173
# --host binds to 0.0.0.0 so the port is reachable from outside the container
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
