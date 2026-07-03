module.exports = {
  apps: [{
    name: '岁蚀写作系统',
    script: 'server.js',
    instances: 1,
    env: {
      PORT: 3001,
      DB_DIR: '.'
    }
  }]
};
