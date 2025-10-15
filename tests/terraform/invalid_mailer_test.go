package test

import (
	"testing"

	"github.com/gruntwork-io/terratest/modules/terraform"
	"github.com/stretchr/testify/assert"
)

func TestInvalidMailer(t *testing.T) {
	t.Parallel()

	mailer := `{
		"role": "arn:aws:iam::123456789012:role/test-role"
	}`

	terraformOptions := &terraform.Options{
		TerraformDir: "../../modules/cloud-custodian-lambda-mailer",
		Vars: map[string]interface{}{
			"mailer": mailer,
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
		assert.Contains(t, errorMessage, "Mailer configuration validation failed", "Should indicate validation failed")
	}
}
