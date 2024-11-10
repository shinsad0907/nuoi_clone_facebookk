const { app, BrowserWindow, ipcMain } = require("electron");
const path = require("path");
const { spawn } = require("child_process");
const { exec } = require("child_process");
let mainWindow;
const fs = require("fs");
const { dialog } = require("electron");

function checkType(value) {
  return typeof value;
}

ipcMain.on("save_editAccount", (event, data) => {
  const jsonString = JSON.stringify(data);
  console.log(jsonString);
  exec(
    `python ./data_processing/ADB.py "save_account_tiktok" "${jsonString.replace(
      /"/g,
      '\\"'
    )}"`,
    (error, stdout, stderr) => {
      if (error) {
        console.error(`Lỗi: ${error.message}`);
        return;
      }
      if (stderr) {
        console.error(`Lỗi stderr: ${stderr}`);
        return;
      }

      // Xử lý đầu ra JSON
      try {
        // Dùng trim() để loại bỏ các khoảng trắng hoặc ký tự xuống dòng
        dialog.showMessageBox({
          type: "info",
          title: "Alert",
          message: `saved account ${stdout}`,
          buttons: ["OK"],
        });
      } catch (e) {
        console.error("Lỗi khi phân tích JSON:", e);
        event.reply("json-parse-error", e.message);
      }
    }
  );
});

// main.js
ipcMain.on("open_web", (event, data) => {
  if (!Array.isArray(data)) {
    console.error("Expected array of account data");
    return;
  }

  console.log("Processing login:", JSON.stringify(data));

  // Khởi tạo tracking object để theo dõi trạng thái của từng tài khoản
  const accountStatus = new Map(
    data.map((acc) => [
      acc.uid,
      {
        id: acc.uid,
        status: "Đang xử lý",
        cookie: "",
      },
    ])
  );

  const pythonProcess = spawn("python", [
    "./data_processing/login_facebook.py",
    JSON.stringify(data),
    "open_account",
  ]);

  // Hàm helper để gửi updates
  const sendStatusUpdate = () => {
    event.reply("login-facebook-status", {
      accounts: Array.from(accountStatus.values()),
    });
  };

  pythonProcess.stdout.on("data", (data) => {
    const lines = data.toString().split("\n");

    for (const line of lines) {
      if (!line.trim()) continue;

      try {
        const logData = JSON.parse(line);
        console.log(logData);

        if (logData.type === "log") {
          // Cập nhật status map và gửi log
          if (logData.id && accountStatus.has(logData.id)) {
            accountStatus.get(logData.id).status =
              logData.status || "Đang xử lý";
            sendStatusUpdate();
          }

          event.reply("process-log", {
            id: logData.id,
            message: logData.message,
            status: logData.status,
          });
        } else if (logData.type === "result" && logData.data) {
          // Cập nhật kết quả cuối cùng cho tài khoản
          if (accountStatus.has(logData.data.id)) {
            accountStatus.set(logData.data.id, {
              id: logData.data.id,
              status: logData.data.status,
              cookie: logData.data.cookie || "",
            });
            sendStatusUpdate();
          }
        }
      } catch (err) {
        console.error("Error parsing Python output:", err);
      }
    }
  });

  pythonProcess.stderr.on("data", (data) => {
    console.error("Python stderr:", data.toString());

    // Cập nhật status thành lỗi cho tất cả tài khoản đang xử lý
    accountStatus.forEach((status, id) => {
      if (status.status === "Đang xử lý") {
        status.status = "Lỗi hệ thống";
      }
    });
    sendStatusUpdate();

    event.reply("process-log", {
      id: "system",
      message: `Error: ${data.toString()}`,
      status: "error",
    });
  });

  pythonProcess.on("close", (code) => {
    if (code !== 0) {
      console.error(`Python process exited with code ${code}`);

      // Cập nhật status thành lỗi cho tất cả tài khoản chưa hoàn thành
      accountStatus.forEach((status, id) => {
        if (status.status === "Đang xử lý") {
          status.status = "Lỗi hệ thống";
        }
      });
      sendStatusUpdate();
      return;
    }

    // Đảm bảo tất cả tài khoản đều có kết quả cuối cùng
    accountStatus.forEach((status, id) => {
      if (status.status === "Đang xử lý") {
        status.status = "Hoàn thành";
      }
    });
    sendStatusUpdate();
  });

  pythonProcess.on("error", (error) => {
    console.error("Failed to start Python process:", error);

    // Cập nhật tất cả tài khoản thành lỗi khởi động
    accountStatus.forEach((status, id) => {
      status.status = "Lỗi khởi động";
    });
    sendStatusUpdate();
  });
});

// Main Process (Electron)
ipcMain.on("run-interaction", (event, data) => {
  console.log("Processing login:", JSON.stringify(data));
  let stdoutData = "";
  let stderrData = "";

  const pythonProcess = spawn("python", [
    "./data_processing/login_facebook.py",
    JSON.stringify(data),
    "run_interaction",
  ]);

  pythonProcess.stdout.on("data", (data) => {
    const lines = data.toString().split("\n");

    for (const line of lines) {
      if (!line.trim()) continue;

      try {
        const logData = JSON.parse(line);
        console.log("Received data from Python:", logData);

        if (logData.type === "log") {
          // Handle log messages
          event.reply("process-log", {
            id: logData.id,
            message: logData.message,
            status: logData.status,
          });

          // Update account status in UI for logs with status
          if (logData.status) {
            event.reply("account-status-update", {
              accountId: logData.id,
              status: logData.message,
              type: "processing",
            });
          }
        } else if (logData.type === "result") {
          // Handle results
          const resultData = logData.data;
          event.reply("account-status-update", {
            accountId: resultData.id,
            status: resultData.status,
            cookie: resultData.cookie || "",
            type: resultData.status.toLowerCase().includes("success")
              ? "success"
              : "error",
          });
        }
      } catch (err) {
        console.warn("Failed to parse Python output:", line, err);
        stdoutData += line + "\n";
      }
    }
  });

  pythonProcess.stderr.on("data", (data) => {
    stderrData += data.toString();
    console.error("Python stderr:", data.toString());

    // Send error to renderer
    event.reply("process-log", {
      id: "system",
      message: `Error: ${data.toString()}`,
      status: "error",
    });
  });

  pythonProcess.on("close", (code) => {
    if (code !== 0) {
      console.error(`Python process exited with code ${code}`);
      // Update all accounts with error status
      data.accounts.forEach((account) => {
        event.reply("account-status-update", {
          accountId: account.uid,
          status: "Lỗi hệ thống",
          type: "error",
        });
      });
      return;
    }

    // Handle any remaining buffered output
    if (stdoutData.trim()) {
      try {
        const finalData = JSON.parse(stdoutData.trim());
        if (Array.isArray(finalData)) {
          finalData.forEach((result) => {
            event.reply("account-status-update", {
              accountId: result.id,
              status: result.status,
              cookie: result.cookie || "",
              type: result.status.toLowerCase().includes("success")
                ? "success"
                : "error",
            });
          });
        }
      } catch (error) {
        console.error("Error parsing final results:", error);
      }
    }
  });

  pythonProcess.on("error", (error) => {
    console.error("Failed to start Python process:", error);
    data.accounts.forEach((account) => {
      event.reply("account-status-update", {
        accountId: account.uid,
        status: "Lỗi khởi động",
        type: "error",
      });
    });
  });
});

ipcMain.on("login_facebook", (event, data) => {
  console.log("Processing login:", JSON.stringify(data));

  const pythonProcess = spawn("python", [
    "./data_processing/login_facebook.py",
    JSON.stringify(data),
    "login_cookie",
  ]);

  let stdoutData = "";
  let stderrData = "";

  // Nhận log và status updates từ Python process
  pythonProcess.stdout.on("data", (data) => {
    console.log(data);
    const lines = data.toString().split("\n");

    for (const line of lines) {
      if (!line.trim()) continue;

      try {
        const logData = JSON.parse(line);
        console.log(logData);
        if (logData.type === "log") {
          // Gửi log về renderer
          event.reply("process-log", {
            id: logData.id,
            message: logData.message,
            status: logData.status,
          });
        } else if (logData.type === "result") {
          // Gửi kết quả về renderer
          event.reply("login-facebook-status", {
            accounts: [logData.data],
          });
        }
      } catch (err) {
        // Nếu không parse được JSON, cộng dồn vào stdoutData
        stdoutData += line + "\n";
      }
    }
  });

  // Nhận error output từ Python
  pythonProcess.stderr.on("data", (data) => {
    stderrData += data.toString();
    console.error("Python stderr:", data.toString());

    // Gửi thông báo lỗi về renderer
    event.reply("process-log", {
      id: "system",
      message: `Error: ${data.toString()}`,
      status: "error",
    });
  });

  // Xử lý khi Python process kết thúc
  pythonProcess.on("close", (code) => {
    if (code !== 0) {
      console.error(`Python process exited with code ${code}`);
      console.error("stderr:", stderrData);

      event.reply("login-facebook-status", {
        accounts: data.map((acc) => ({
          id: acc.uid,
          status: "Lỗi hệ thống",
          cookie: "",
        })),
      });
      return;
    }

    // Xử lý kết quả cuối cùng nếu có
    if (stdoutData.trim()) {
      try {
        const results = JSON.parse(stdoutData.trim());
        console.log("Login results:", results);

        // Gửi kết quả về renderer
        if (Array.isArray(results)) {
          event.reply("login-facebook-status", { accounts: results });

          results.forEach((result) => {
            event.reply("login-facebook-status", {
              accounts: data.map((acc) => ({
                id: acc.uid,
                status: result.status,
                cookie: result.cookie || "",
              })),
            });
          });
        }
      } catch (error) {
        console.error("Error parsing final results:", error);
        event.reply("login-facebook-status", {
          accounts: data.map((acc) => ({
            id: acc.uid,
            status: "Lỗi dữ liệu",
            cookie: "",
          })),
        });
      }
    }
  });

  // Xử lý lỗi khi khởi động Python process
  pythonProcess.on("error", (error) => {
    console.error("Failed to start Python process:", error);
    event.reply("login-facebook-status", {
      accounts: data.map((acc) => ({
        id: acc.uid,
        status: "Lỗi khởi động",
        cookie: "",
      })),
    });
  });
});

ipcMain.on("create_app_group", (event, data) => {
  const jsonString = JSON.stringify(data);
  console.log(jsonString);
  exec(
    `python ./data_processing/ADB.py "create_groups_account" "${jsonString.replace(
      /"/g,
      '\\"'
    )}"`,
    (error, stdout, stderr) => {
      if (error) {
        console.error(`Lỗi: ${error.message}`);
        return;
      }
      if (stderr) {
        console.error(`Lỗi stderr: ${stderr}`);
        return;
      }

      // Xử lý đầu ra JSON
      try {
        // Dùng trim() để loại bỏ các khoảng trắng hoặc ký tự xuống dòng
        dialog.showMessageBox({
          type: "info",
          title: "Alert",
          message: `${stdout}`,
          buttons: ["OK"],
        });
      } catch (e) {
        console.error("Lỗi khi phân tích JSON:", e);
        event.reply("json-parse-error", e.message);
      }
    }
  );
});

ipcMain.on("save_account", (event, data) => {
  // Chạy script Python và truyền dữ liệu qua command line arguments
  const jsonString = JSON.stringify(data);
  console.log(jsonString);
  exec(
    `python ./data_processing/ADB.py  "save_account_tiktok" "${jsonString.replace(
      /"/g,
      '\\"'
    )}"`,
    (error, stdout, stderr) => {
      if (error) {
        console.error(`Lỗi: ${error.message}`);
        return;
      }
      if (stderr) {
        console.error(`Lỗi stderr: ${stderr}`);
        return;
      }

      // Xử lý đầu ra JSON
      try {
        // const devices = JSON.parse(stdout); // Chuyển đổi stdout thành JSON
        console.log(`Kết quả: ${stdout}`);
        // Gửi dữ liệu trở lại cho renderer process
      } catch (e) {
        console.error("Lỗi khi phân tích JSON:", e);
        // Gửi thông báo lỗi đến renderer process
        event.reply("json-parse-error", e.message);
      }
    }
  );
});
// read json file
ipcMain.on("get_devices", (event) => {
  // Chạy script Python và truyền dữ liệu qua command line arguments
  exec(
    `python ./data_processing/ADB.py "information_device"`,
    (error, stdout, stderr) => {
      if (error) {
        console.error(`Lỗi: ${error.message}`);
        return;
      }
      if (stderr) {
        console.error(`Lỗi stderr: ${stderr}`);
        return;
      }

      // Xử lý đầu ra JSON
      try {
        const devices = JSON.parse(stdout); // Chuyển đổi stdout thành JSON
        console.log(`Kết quả: ${devices}`);
        // Gửi dữ liệu trở lại cho renderer process
        event.reply("infomation_devices", devices); // Change the event name here
      } catch (e) {
        console.error("Lỗi khi phân tích JSON:", e);
      }
    }
  );
});
ipcMain.on("get_application_tiktok", (event) => {
  // Chạy script Python và truyền dữ liệu qua command line arguments
  exec(
    `python ./data_processing/ADB.py "application_tiktok"`,
    (error, stdout, stderr) => {
      if (error) {
        console.error(`Lỗi: ${error.message}`);
        return;
      }
      if (stderr) {
        console.error(`Lỗi stderr: ${stderr}`);
        return;
      }

      // Xử lý đầu ra JSON
      try {
        const devices = JSON.parse(stdout); // Chuyển đổi stdout thành JSON
        console.log(`Kết quả: ${devices}`);
        // Gửi dữ liệu trở lại cho renderer process
        event.reply("get_application_tiktoks", devices);
      } catch (e) {
        console.error("Lỗi khi phân tích JSON:", e);
      }
    }
  );
});
ipcMain.on("get-json-data", (event) => {
  fs.readFile("./data/action.json", "utf8", (err, data) => {
    if (err) {
      console.error("Error reading JSON file:", err);
      event.reply("json-data", null);
    } else {
      const jsonData = JSON.parse(data);
      event.reply("json-data", jsonData);
    }
  });
});
ipcMain.on("add_device_button", () => {
  add_device_button(); // Gọi hàm mở tab mới
});
ipcMain.on("run_interactively", (event, accountsData) => {
  const newTab = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
    },
  });

  newTab.loadFile(path.join(__dirname, "./src/temples", "interaction.html"));
  newTab.webContents.openDevTools();

  newTab.webContents.on("did-finish-load", () => {
    newTab.webContents.send("accounts-data", accountsData);
  });
});

ipcMain.on("createAction", () => {
  addAction(); // Gọi hàm mở tab mới
});
ipcMain.on("settingaction", () => {
  settingaction(); // Gọi hàm mở tab mới
});
ipcMain.on("save_settingaction", (event, data) => {
  // Chạy script Python và truyền dữ liệu qua command line arguments
  const jsonString = JSON.stringify(data);
  console.log(data);
  exec(
    `python ./data_processing/python_bridge.py "${jsonString.replace(
      /"/g,
      '\\"'
    )}" "save_settingaction"`,
    (error, stdout, stderr) => {
      // ...
      if (error) {
        console.error(`Lỗi: ${error.message}`);
        return;
      }
      if (stderr) {
        console.error(`Lỗi stderr: ${stderr}`);
        return;
      }
      console.log(`Kết quả: ${stdout}`);
      // Gửi dữ liệu trở lại cho renderer process nếu cần
      event.reply("action-response", stdout);
    }
  );
});

ipcMain.on("save_file_account", (event, data) => {
  // Chạy script Python và truyền dữ liệu qua command line arguments
  const jsonString = JSON.stringify(data);
  console.log(jsonString);
  exec(
    `python ./data_processing/ADB.py "save_file_account" "${jsonString.replace(
      /"/g,
      '\\"'
    )}" `,
    (error, stdout, stderr) => {
      if (error) {
        console.error(`Lỗi: ${error.message}`);
        return;
      }
      if (stderr) {
        console.error(`Lỗi stderr: ${stderr}`);
        return;
      }
      dialog.showMessageBox({
        type: "info",
        title: "Alert",
        message: `${stdout}`,
        buttons: ["OK"],
      });
      // Gửi dữ liệu trở lại cho renderer process nếu cần
      event.reply("action-response", stdout);
    }
  );
});

ipcMain.on("add_manual_account", (event, data) => {
  // Chạy script Python và truyền dữ liệu qua command line arguments
  const jsonString = JSON.stringify(data);
  console.log(jsonString);
  exec(
    `python ./data_processing/ADB.py "save_account_facebook" "${jsonString.replace(
      /"/g,
      '\\"'
    )}" `,
    (error, stdout, stderr) => {
      if (error) {
        console.error(`Lỗi: ${error.message}`);
        return;
      }
      if (stderr) {
        console.error(`Lỗi stderr: ${stderr}`);
        return;
      }
      console.log(`Kết quả: ${stdout}`);
      // Gửi dữ liệu trở lại cho renderer process nếu cần
      event.reply("action-response", stdout);
    }
  );
});

ipcMain.on("savename_action", (event, data, action) => {
  // Chạy script Python và truyền dữ liệu qua command line arguments
  console.log(action, data);
  exec(
    `python ./data_processing/python_bridge.py "${data}" "create_nameaction"`,
    (error, stdout, stderr) => {
      if (error) {
        console.error(`Lỗi: ${error.message}`);
        return;
      }
      if (stderr) {
        console.error(`Lỗi stderr: ${stderr}`);
        return;
      }
      console.log(`Kết quả: ${stdout}`);
      // Gửi dữ liệu trở lại cho renderer process nếu cần
      event.reply("action-response", stdout);
    }
  );
});
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
    },
  });

  mainWindow.loadFile("index.html"); // Tệp HTML chính của bạn
  // mainWindow.webContents.openDevTools();

  // Mở DevTools (nếu cần)
  // mainWindow.webContents.openDevTools();
}

function add_device_button() {
  const newTab = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
    },
  });

  newTab.loadFile(path.join(__dirname, "./src/temples", "settingdevice.html")); // Điều chỉnh đường dẫn cho đúng
  newTab.webContents.openDevTools();
}
// Hàm để mở cửa sổ mới
function openNewTab() {
  const newTab = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
    },
  });

  newTab.loadFile(path.join(__dirname, "./src/temples", "interaction.html")); // Điều chỉnh đường dẫn cho đúng
  newTab.webContents.openDevTools();
  // Gửi dữ liệu vào tab mới sau khi nó đã hoàn thành tải
}

// Hàm để mở cửa sổ mới
function addAction(actionName) {
  const newTab = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
    },
  });

  newTab.loadFile(path.join(__dirname, "./src/temples", "addAction.html")); // Điều chỉnh đường dẫn cho đúng
  newTab.webContents.openDevTools();
}

// Hàm để mở cửa sổ mới
function settingaction() {
  const newTab = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
    },
  });

  newTab.loadFile(path.join(__dirname, "./src/temples", "settingaction.html")); // Điều chỉnh đường dẫn cho đúng
}

// Xuất hàm để có thể gọi từ renderer process
module.exports = { openNewTab, addAction, settingaction };

app.whenReady().then(createWindow);

// Đảm bảo chỉ có một cửa sổ nếu có yêu cầu mới
app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});
