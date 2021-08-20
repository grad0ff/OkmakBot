FROM Python
WORKDIR /root/project/okmakbot
EXPOSE 3000
COPY ./ ./
RUN npm install
CMD ["python", "start"]