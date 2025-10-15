package test

import (
	"testing"

	"github.com/gruntwork-io/terratest/modules/terraform"
	"github.com/stretchr/testify/assert"
)

func TestInvalidPolicy(t *testing.T) {
	t.Parallel()

	policies := `{
		"policies": [
			{
				"name": "test-invalid-mode",
				"resource": "ec2",
				"filters": [{"State.Name": "running"}],
				"actions": [{"type": "stop"}],
				"mode": {
					"type": "invalid-mode",
					"role": "arn:aws:iam::123456789012:role/test-role"
				}
			}
		]
	}`

	terraformOptions := &terraform.Options{
		TerraformDir: "../../",
		Vars: map[string]interface{}{
			"policies":          policies,
			"execution_options": map[string]interface{}{},
		},
		NoColor: true,
	}

	defer terraform.Destroy(t, terraformOptions)

	terraform.Init(t, terraformOptions)

	_, err := terraform.PlanE(t, terraformOptions)
	assert.Error(t, err, "Expected terraform plan to fail with validation error")

	if err != nil {
		errorMessage := err.Error()
		assert.Contains(t, errorMessage, "External Program Execution Failed", "Should fail due to external program error")
		assert.Contains(t, errorMessage, "Policy validation failed", "Should indicate validation failed")
		assert.Contains(t, errorMessage, "Policy mode must be one of", "Should show available policy modes")
		assert.Contains(t, errorMessage, "invalid-mode", "Should mention the invalid mode that was provided")
		assert.Contains(t, errorMessage, "Policy validation error", "Should show Cloud Custodian validation error")
	}
}
