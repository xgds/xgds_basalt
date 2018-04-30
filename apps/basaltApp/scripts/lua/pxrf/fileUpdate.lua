dirRoot = "/Data"
snapshotFile = "/filesnapshot.txt"

local function waitWlanConnect()
    while 1 do
        local res = fa.ReadStatusReg()
        local a = string.sub(res, 13, 16)
        a = tonumber(a, 16)
        if (bit32.extract(a, 15) == 1) then
            print("connect")
            break
        end
        if (bit32.extract(a, 0) == 1) then
            print("mode Bridge")
            break
        end
        if (bit32.extract(a, 12) == 1) then
            print("mode AP")
            break
        end
        sleep(2000)
    end
end

local function maxModTime(dirRoot)
  maxMod = 0
  for aFile in lfs.dir(dirRoot) do
    mod_val = lfs.attributes(aFile, "modification")
    if mod_val > maxMod then
      maxMod = mod_val
    end
  end
  return maxMod
end

local function lastModFile(dirRoot, maxTime)
  for aFile in lfs.dir(dirRoot) do
    mod_val = lfs.attributes(aFile, "modification")
    if mod_val > maxTime then
      newMod = mod_val
      newFile = aFile
    end
  end
  return newMod, newFile
end

local function writeCurrentFileList(dirRoot, snapshotFile)
  wFile = io.open(snapshotFile, "w")
  for aFile in lfs.dir(dirRoot) do
    wFile:write(aFile.."\n")
  end
  io.close(wFile)
end

local function appendCurrentFileList(snapshotFile, newFile)
  wFile = io.open(snapshotFile, "a")
  wFile:write(newFile.."\n")
  io.close(wFile)
end

local function buildFileSet(snapshotFile)
  fileSet = {}
  for line in io.lines(snapshotFile) do
    fileSet[line] = true
  end
  return fileSet
end

local function getFileDiffs(dirRoot, fileSet)
  newFileList = {}
  for aFile in lfs.dir(dirRoot) do
    if not fileSet[aFile] then
      table.insert(newFileList, aFile)
    end
  end
  return newFileList
end

local function uploadFile(dirPath, fileName, fileLabel, mimeType, uploadUrl, snapshotFile)
    local boundary = 'bnfDxpKY69NKk'
    local headers = {}
    local place_holder = '<!--WLANSDFILE-->'

    headers['Connection'] = 'close'
    headers['Content-Type'] = 'multipart/form-data; boundary="'..boundary..'"'
    headers['Authorization'] = 'Basic TODO PYTHON base64.b64encode(username:token)'

    local body = '--' .. boundary..'\r\n'
        ..'Content-Disposition: form-data; name="username"\r\n\r\n'..'ev2'
        .. '\r\n--' .. boundary .. '\r\n'
        ..'Content-Disposition: form-data; name="vehicle"\r\n\r\n'..'2'
        .. '\r\n--' .. boundary .. '\r\n'
        ..'Content-Disposition: form-data; name="timezone"\r\n\r\n'
        .. 'US/Hawaii'
        .. '\r\n--' .. boundary .. '\r\n'
        ..'Content-Disposition: form-data; name="relay"\r\n\r\n'..'true'
        .. '\r\n--' .. boundary .. '\r\n'
        ..'Content-Disposition: form-data; name='..fileLabel..'; filename="'
        ..fileName..'"\r\n'
        ..'Content-Type: '..mimeType..'\r\n\r\n'
        ..'<!--WLANSDFILE-->\r\n'
        .. '--' .. boundary .. '--\r\n'

    headers['Content-Length'] =
        lfs.attributes(dirPath.."/"..fileName, 'size')
        + string.len(body)
        - string.len(place_holder)
    local args = {}
    args["url"] = uploadUrl
    args["method"] = "POST"
    args["headers"] = headers
    args["body"] = body
    args["file"] = dirPath.."/"..fileName
    args["bufsize"] = 1460*8
    local b,c,h = fa.request(args)
    b, h = nil,nil
    collectgarbage()
    if (c ~= 200) then
        return c
    end
    return c
end


sFile = io.open(snapshotFile, "r")
if not sFile then
  writeCurrentFileList(dirRoot, snapshotFile)
  newFileList = {}
  b,c,h = "-None-\n", "-None-\n", "-None-\n"
else
  io.close(sFile)
  fileSet = buildFileSet(snapshotFile)
  newFileList = getFileDiffs(dirRoot, fileSet)
--  writeCurrentFileList(dirRoot, snapshotFile)
end
  

c = uploadFile(dirRoot, "Results.csv", "elementResultsCsvFile", "text/csv", "http://10.10.24.72/basaltApp/savePxrfElementFile/", snapshotFile)

for index, file in ipairs(newFileList) do
  c = uploadFile(dirRoot, file, "manufacturerDataFile", "application/octet-stream", "http://10.10.24.72/basaltApp/savePxrfMfgFile/", snapshotFile)
  if c == 200 then
    appendCurrentFileList(snapshotFile, file)
--    writeCurrentFileList(dirRoot, snapshotFile)
  end
  fa.sharedmemory("write",0,22,string.format("Last Status %010d", c))
end


print("HTTP/1.1 200 OK\r\n")
print("<HTML>")
print("<HEAD>")
print("<TITLE>Upload Page</TITLE>")
print("</HEAD>")
print("<BODY style='font-family:helvetica;'>")
print("Status code:")
print(c)
print("</pre>")
print("</BODY>")
print("</HTML>")
