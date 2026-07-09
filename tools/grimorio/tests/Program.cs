using MCR.Grimorio.Core;

var result = OtbmReader.RunSelfTest();
Console.WriteLine(result ? "OTBM Parser: All tests passed!" : "OTBM Parser: Tests FAILED!");
return result ? 0 : 1;
