$root = 'D:/projects/WindPowerForcast'
$python = '/home/ljpy/projects/amd-rocm-pytorch-wsl/.venv/bin/python'
$configs = @(
  @{Name='h08_z08'; Hidden=8; Latent=8; LR='0.0005'},
  @{Name='h16_z16'; Hidden=16; Latent=16; LR='0.001'},
  @{Name='h32_z16'; Hidden=32; Latent=16; LR='0.001'}
)
foreach ($c in $configs) {
  $out = "outputs/detection_hpo_v16/$($c.Name)"
  wsl.exe -d Ubuntu-24.04 --cd /mnt/d/projects/WindPowerForcast -e $python script/benchmark_detection_v9.py --epochs 30 --seeds 41 42 43 --models timesnet kanad --hidden $($c.Hidden) --latent-dim $($c.Latent) --learning-rate $($c.LR) --output-dir $out
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
