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
    print(aFile, mod_val)
    if mod_val > maxTime then
      newMod = mod_val
      newFile = aFile
    end
  end
  return newMod, newFile
end

local function writeCurrentFileList(dirRoot)
  wFile = io.open("/filesnapshot.txt", "w")
  for aFile in lfs.dir(dirRoot) do
    wFile:write(aFile.."\n")
  end
  io.close(wFile)
end

print("<HTML>")
print("<HEAD>")
print("<TITLE>My cool test page</TITLE>")
print("</HEAD>")
print("<BODY style='font-family:helvetica;'>")
print("My Lua version:", _VERSION, "<br/>")
print("I have " .. #arg .. " arguments<br/>")
for i=1,#arg do
  print(arg[i].."<br/>")
end
mod_val = lfs.attributes("/test.lua", "modification")
print("My mod time: " .. mod_val .. "<br/>")
res = fa.sharedmemory("read", 0, 22, 0)
print("shared memory:", res, "(" .. string.len(res)..")", "<br/>")
print("division:", (323-323%256)/256, "<br/>")
rFile = io.open("/filesnapshot.txt", "r")
rData = rFile:read("*all")
io.close(rFile)
print("<pre>")
-- print(rData)
-- writeCurrentFileList("/DCIM/102OLYMP")
-- print("File loop...")
-- for aFile in lfs.dir("/DCIM/102OLYMP") do
--   mod_val = lfs.attributes(aFile, "size")
--   print(aFile, mod_val)
-- end
print("Snapshot File:")
print(rData)
--print("Status File:")
--for line in io.lines("/mystatus.txt") do
--  print(line)
--end
--maxtl1 = maxModTime("/DCIM/102OLYMP") - 1
--newTime, newFile = lastModFile("/DCIM/102OLYMP", maxtl1)
-- fa.sharedmemory("write",0,10,string.format("%010d", maxtl1))
--print(newTime, newFile)
print("Done!")
print("</pre>")
print("</BODY>")
print("</HTML>")
print("")

-- my comment here keeps going on
