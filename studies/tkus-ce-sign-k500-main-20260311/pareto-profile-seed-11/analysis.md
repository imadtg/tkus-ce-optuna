# Pareto Profile Analysis

- Profile directory: `/home/pc/Desktop/tkus-ce-optuna/studies/tkus-ce-sign-k500-main-20260311/pareto-profile-seed-11`
- Profiled trials: `20`

## Aggregate Self Hotspots

- `NGramModel.sampleItemset`: `6428` samples
- `java.util.HashMap.getNode`: `3789` samples
- `java.util.HashMap$HashIterator.nextNode`: `2685` samples
- `java.util.BitSet.nextSetBit`: `2644` samples
- `NGramModel.getContextItems`: `2464` samples
- `NGramModel.getItemProbability`: `1777` samples
- `java.util.HashMap$HashIterator.<init>`: `1171` samples
- `Particle.matchItemset`: `548` samples
- `Particle.computeExtensionFromParent`: `494` samples
- `java.util.ArrayList.sort`: `387` samples
- `java.lang.Integer.equals`: `283` samples
- `java.util.Random.nextInt`: `248` samples

## Runtime-Band Hotspots

### Fast
- `NGramModel.sampleItemset`: mean self-sample share `19.94%`
- `Particle.computeExtensionFromParent`: mean self-sample share `8.13%`
- `java.util.BitSet.nextSetBit`: mean self-sample share `7.18%`
- `Particle.matchItemset`: mean self-sample share `6.97%`
- `java.util.HashMap.getNode`: mean self-sample share `5.47%`
- `java.util.HashMap$HashIterator.nextNode`: mean self-sample share `3.94%`
- `java.lang.Integer.equals`: mean self-sample share `2.77%`
- `NGramModel.getItemProbability`: mean self-sample share `2.70%`

### Mid
- `NGramModel.sampleItemset`: mean self-sample share `25.71%`
- `java.util.BitSet.nextSetBit`: mean self-sample share `14.01%`
- `java.util.HashMap$HashIterator.nextNode`: mean self-sample share `11.73%`
- `java.util.HashMap.getNode`: mean self-sample share `6.44%`
- `Particle.matchItemset`: mean self-sample share `5.85%`
- `NGramModel.getItemProbability`: mean self-sample share `5.22%`
- `NGramModel.getContextItems`: mean self-sample share `4.83%`
- `java.util.HashMap$HashIterator.<init>`: mean self-sample share `4.31%`

### Heavy
- `NGramModel.sampleItemset`: mean self-sample share `24.83%`
- `java.util.HashMap.getNode`: mean self-sample share `20.79%`
- `NGramModel.getContextItems`: mean self-sample share `12.88%`
- `java.util.HashMap$HashIterator.nextNode`: mean self-sample share `10.75%`
- `java.util.BitSet.nextSetBit`: mean self-sample share `8.10%`
- `NGramModel.getItemProbability`: mean self-sample share `8.06%`
- `java.util.HashMap$HashIterator.<init>`: mean self-sample share `4.38%`
- `java.util.ArrayList.sort`: mean self-sample share `1.16%`

## Function Correlations

- `NGramModel.sampleItemset`: runtime Pearson `0.120`, utility Pearson `0.483`
- `java.util.HashMap.getNode`: runtime Pearson `0.590`, utility Pearson `0.459`
- `java.util.HashMap$HashIterator.nextNode`: runtime Pearson `0.245`, utility Pearson `0.360`
- `java.util.BitSet.nextSetBit`: runtime Pearson `0.021`, utility Pearson `0.257`
- `NGramModel.getContextItems`: runtime Pearson `0.680`, utility Pearson `0.519`
- `NGramModel.getItemProbability`: runtime Pearson `0.441`, utility Pearson `0.409`
- `java.util.HashMap$HashIterator.<init>`: runtime Pearson `0.221`, utility Pearson `0.369`
- `Particle.matchItemset`: runtime Pearson `-0.293`, utility Pearson `-0.208`
- `Particle.computeExtensionFromParent`: runtime Pearson `-0.610`, utility Pearson `-0.860`
- `java.util.ArrayList.sort`: runtime Pearson `-0.025`, utility Pearson `0.330`
- `java.lang.Integer.equals`: runtime Pearson `-0.152`, utility Pearson `0.061`
- `java.util.Random.nextInt`: runtime Pearson `0.435`, utility Pearson `0.520`

## Per-Trial Top Self Hotspots

### Trial 82 (`0.630s`, `1471.067`)
- `java.util.BitSet.nextSetBit`: `11.11%`
- `Particle.computeExtensionFromParent`: `9.88%`
- `java.util.HashMap$HashIterator.nextNode`: `6.17%`
- `NGramModel.sampleItemset`: `6.17%`
- `NGramModel.getContextItems`: `6.17%`
- `AlgoTKUSCE.buildFilteredDatabase`: `4.94%`
- `AlgoTKUSCE.parseSequenceLine`: `3.70%`
- `java.util.HashMap.getNode`: `3.70%`

### Trial 46 (`0.662s`, `2075.478`)
- `AlgoTKUSCE.buildFilteredDatabase`: `8.16%`
- `NGramModel.sampleItemset`: `8.16%`
- `Particle.computeExtensionFromParent`: `8.16%`
- `java.util.HashMap.getNode`: `8.16%`
- `AlgoTKUSCE.buildUtilitySummaries`: `4.08%`
- `Particle.init`: `4.08%`
- `Particle.computeRootExtensionList`: `4.08%`
- `java.util.BitSet.nextSetBit`: `4.08%`

### Trial 63 (`0.880s`, `3001.112`)
- `java.util.BitSet.nextSetBit`: `19.44%`
- `Particle.computeExtensionFromParent`: `11.11%`
- `java.util.HashMap$HashIterator.nextNode`: `5.56%`
- `Particle.matchItemset`: `5.56%`
- `NGramModel.getItemProbability`: `4.63%`
- `NGramModel.getContextItems`: `4.63%`
- `Particle.init`: `3.70%`
- `NGramModel.sampleItemset`: `3.70%`

### Trial 33 (`1.146s`, `3221.284`)
- `Particle.matchItemset`: `14.71%`
- `Particle.computeExtensionFromParent`: `11.76%`
- `NGramModel.getItemProbability`: `9.80%`
- `java.util.BitSet.nextSetBit`: `5.88%`
- `NGramModel.sampleItemset`: `5.88%`
- `java.util.HashMap$HashIterator.nextNode`: `4.90%`
- `java.util.HashMap.merge`: `3.92%`
- `Particle.computeRootExtensionList`: `3.92%`

### Trial 40 (`1.196s`, `3553.075`)
- `NGramModel.sampleItemset`: `16.26%`
- `Particle.matchItemset`: `16.26%`
- `java.util.HashMap$HashIterator.nextNode`: `14.63%`
- `Particle.computeExtensionFromParent`: `5.69%`
- `NGramModel.getItemProbability`: `5.69%`
- `AlgoTKUSCE.buildFilteredDatabase`: `2.44%`
- `java.util.HashMap.resize`: `2.44%`
- `jdk.internal.classfile.impl.StackCounter.<init>`: `1.63%`

### Trial 172 (`1.330s`, `5355.121`)
- `Particle.matchItemset`: `15.35%`
- `java.util.HashMap$HashIterator.<init>`: `10.23%`
- `NGramModel.sampleItemset`: `8.84%`
- `Particle.computeExtensionFromParent`: `8.37%`
- `java.util.HashMap$HashIterator.nextNode`: `6.05%`
- `NGramModel.getContextItems`: `5.12%`
- `java.util.HashMap.getNode`: `5.12%`
- `NGramModel.getItemProbability`: `4.65%`

### Trial 97 (`1.858s`, `6083.613`)
- `NGramModel.sampleItemset`: `37.55%`
- `java.lang.Integer.equals`: `15.10%`
- `Particle.matchItemset`: `9.39%`
- `Particle.computeExtensionFromParent`: `5.31%`
- `java.util.ArrayList.sort`: `2.86%`
- `java.util.HashMap.getNode`: `2.86%`
- `java.util.BitSet.nextSetBit`: `2.04%`
- `AlgoTKUSCE.samplePopulation`: `2.04%`

### Trial 4 (`2.022s`, `6195.454`)
- `NGramModel.sampleItemset`: `39.08%`
- `java.lang.Integer.equals`: `12.61%`
- `Particle.matchItemset`: `7.14%`
- `Particle.computeExtensionFromParent`: `3.78%`
- `java.util.BitSet.nextSetBit`: `2.52%`
- `java.util.ArrayList.sort`: `2.52%`
- `AlgoTKUSCE.samplePopulation`: `2.10%`
- `AlgoTKUSCE.buildFilteredDatabase`: `1.26%`

### Trial 38 (`2.072s`, `6438.478`)
- `NGramModel.sampleItemset`: `35.66%`
- `java.util.HashMap.getNode`: `19.67%`
- `Particle.computeExtensionFromParent`: `9.84%`
- `java.util.BitSet.nextSetBit`: `9.43%`
- `AlgoTKUSCE.buildFilteredDatabase`: `1.23%`
- `java.util.HashMap.resize`: `1.23%`
- `Particle.computeFitnessFromExtList`: `1.23%`
- `java.util.ArrayList.grow`: `0.82%`

### Trial 179 (`2.258s`, `6930.060`)
- `NGramModel.sampleItemset`: `38.13%`
- `java.util.BitSet.nextSetBit`: `14.05%`
- `java.util.HashMap.getNode`: `13.38%`
- `Particle.computeExtensionFromParent`: `7.36%`
- `java.util.ArrayList.sort`: `2.01%`
- `java.util.HashMap$HashIterator.<init>`: `1.67%`
- `AlgoTKUSCE.buildFilteredDatabase`: `1.34%`
- `Particle.matchItemset`: `1.34%`

### Trial 93 (`3.520s`, `7609.038`)
- `NGramModel.sampleItemset`: `22.20%`
- `java.util.HashMap$HashIterator.nextNode`: `20.52%`
- `java.util.BitSet.nextSetBit`: `18.66%`
- `NGramModel.getItemProbability`: `5.41%`
- `Particle.computeExtensionFromParent`: `5.04%`
- `NGramModel.getContextItems`: `4.66%`
- `java.util.HashMap$HashIterator.<init>`: `3.17%`
- `java.util.HashMap.getNode`: `2.80%`

### Trial 62 (`3.672s`, `7693.552`)
- `NGramModel.sampleItemset`: `21.43%`
- `java.util.HashMap$HashIterator.nextNode`: `18.34%`
- `java.util.BitSet.nextSetBit`: `16.07%`
- `NGramModel.getItemProbability`: `8.44%`
- `java.util.HashMap.getNode`: `4.87%`
- `java.util.HashMap$HashIterator.<init>`: `4.06%`
- `NGramModel.getContextItems`: `3.41%`
- `Particle.computeExtensionFromParent`: `3.25%`

### Trial 10 (`4.358s`, `7933.919`)
- `NGramModel.sampleItemset`: `23.83%`
- `java.util.BitSet.nextSetBit`: `19.13%`
- `java.lang.Integer.equals`: `9.56%`
- `java.util.HashMap$HashIterator.nextNode`: `9.40%`
- `NGramModel.getItemProbability`: `5.54%`
- `AlgoTKUSCE.samplePopulation`: `4.70%`
- `java.util.HashMap$HashIterator.<init>`: `3.36%`
- `Particle.computeExtensionFromParent`: `3.19%`

### Trial 41 (`5.336s`, `8572.199`)
- `Particle.matchItemset`: `24.93%`
- `NGramModel.sampleItemset`: `19.83%`
- `java.util.HashMap.getNode`: `13.70%`
- `NGramModel.getContextItems`: `12.10%`
- `java.util.HashMap$HashIterator.nextNode`: `5.83%`
- `Particle.computeExtensionFromParent`: `3.94%`
- `java.util.BitSet.nextSetBit`: `1.60%`
- `java.util.HashMap.resize`: `1.31%`

### Trial 177 (`6.082s`, `8664.474`)
- `NGramModel.sampleItemset`: `48.40%`
- `java.util.HashMap.getNode`: `19.46%`
- `Particle.matchItemset`: `13.87%`
- `Particle.computeExtensionFromParent`: `2.59%`
- `java.util.ArrayList.sort`: `1.60%`
- `java.util.BitSet.nextSetBit`: `1.40%`
- `AlgoTKUSCE.samplePopulation`: `0.90%`
- `AlgoTKUSCE.insertTopList`: `0.90%`

### Trial 20 (`10.098s`, `9603.989`)
- `NGramModel.sampleItemset`: `30.62%`
- `java.util.HashMap$HashIterator.nextNode`: `18.78%`
- `java.util.BitSet.nextSetBit`: `17.17%`
- `NGramModel.getItemProbability`: `6.66%`
- `java.util.HashMap.getNode`: `3.85%`
- `Particle.computeExtensionFromParent`: `2.94%`
- `java.util.HashMap$HashIterator.<init>`: `2.66%`
- `java.util.ArrayList.sort`: `2.45%`

### Trial 3 (`10.412s`, `10012.924`)
- `java.util.BitSet.nextSetBit`: `20.72%`
- `NGramModel.sampleItemset`: `19.14%`
- `java.util.HashMap$HashIterator.<init>`: `17.07%`
- `NGramModel.getContextItems`: `9.96%`
- `NGramModel.getItemProbability`: `7.05%`
- `java.util.HashMap$HashIterator.nextNode`: `7.05%`
- `Particle.computeExtensionFromParent`: `2.73%`
- `java.util.ArrayList.sort`: `2.31%`

### Trial 176 (`10.766s`, `11316.256`)
- `NGramModel.sampleItemset`: `20.26%`
- `java.util.BitSet.nextSetBit`: `17.33%`
- `java.util.HashMap$HashIterator.nextNode`: `13.35%`
- `NGramModel.getItemProbability`: `8.69%`
- `NGramModel.getContextItems`: `8.50%`
- `java.lang.Integer.equals`: `7.39%`
- `java.util.HashMap$HashIterator.<init>`: `4.18%`
- `java.util.HashMap.getNode`: `3.84%`

### Trial 0 (`45.644s`, `11868.233`)
- `NGramModel.sampleItemset`: `25.75%`
- `java.util.HashMap.getNode`: `22.03%`
- `NGramModel.getContextItems`: `13.14%`
- `java.util.HashMap$HashIterator.nextNode`: `9.43%`
- `java.util.BitSet.nextSetBit`: `8.10%`
- `NGramModel.getItemProbability`: `7.80%`
- `java.util.HashMap$HashIterator.<init>`: `4.00%`
- `java.util.ArrayList.sort`: `0.98%`

### Trial 39 (`46.812s`, `12373.958`)
- `NGramModel.sampleItemset`: `23.91%`
- `java.util.HashMap.getNode`: `19.54%`
- `NGramModel.getContextItems`: `12.63%`
- `java.util.HashMap$HashIterator.nextNode`: `12.07%`
- `NGramModel.getItemProbability`: `8.32%`
- `java.util.BitSet.nextSetBit`: `8.09%`
- `java.util.HashMap$HashIterator.<init>`: `4.77%`
- `java.util.Random.nextInt`: `1.53%`

