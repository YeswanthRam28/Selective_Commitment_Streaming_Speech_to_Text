
param([string]$Text, [string]$OutPath, [int]$Rate)
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.Rate = $Rate
$synth.SetOutputToWaveFile($OutPath)
$synth.Speak($Text)
$synth.Dispose()
